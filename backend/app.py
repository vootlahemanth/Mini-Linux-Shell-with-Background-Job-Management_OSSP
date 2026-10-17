from __future__ import annotations

import os
import shlex
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
WORKSPACE = ROOT / "workspace"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
WORKSPACE.mkdir(exist_ok=True)
AUDIT_LOG = DATA / "audit.log"

app = Flask(__name__, static_folder=None)
app.config["JSON_SORT_KEYS"] = False

# Commands that are safe enough for a local teaching demo. Never pass user text to a shell.
ALLOWED = {"pwd", "date", "whoami", "hostname", "ls", "echo", "sleep", "uptime", "uname", "cat"}
MAX_COMMAND_LENGTH = 500
MAX_ARGS = 32
MAX_SLEEP_SECONDS = 300
jobs: dict[int, dict[str, Any]] = {}
next_job_id = 1
lock = threading.RLock()


def audit(event: str, **details: Any) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **details,
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(__import__("json").dumps(record, ensure_ascii=False) + "\n")


def parse_command(raw: str) -> list[str]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Enter a command.")
    if len(raw) > MAX_COMMAND_LENGTH:
        raise ValueError("Command is too long.")
    # Shell metacharacters are rejected rather than interpreted.
    forbidden = [";", "|", ">", "<", "`", "$(", "&&", "||", "\n", "\r"]
    if any(part in raw for part in forbidden):
        raise ValueError("Shell operators, pipes, redirects, and command chaining are not supported.")
    try:
        args = shlex.split(raw, posix=True)
    except ValueError as exc:
        raise ValueError(f"Could not parse command: {exc}") from exc
    if not args:
        raise ValueError("Enter a command.")
    if len(args) > MAX_ARGS:
        raise ValueError(f"Use at most {MAX_ARGS} arguments.")
    if args[0] not in ALLOWED:
        raise ValueError(f"'{args[0]}' is not allowed. Try help.")
    if args[0] == "sleep":
        if len(args) != 2:
            raise ValueError("Usage: sleep SECONDS (maximum 300).")
        try:
            seconds = float(args[1])
        except ValueError as exc:
            raise ValueError("sleep expects a number of seconds.") from exc
        if seconds < 0 or seconds > MAX_SLEEP_SECONDS:
            raise ValueError("sleep duration must be between 0 and 300 seconds.")
    if args[0] == "cat":
        if len(args) != 2:
            raise ValueError("Usage: cat FILENAME (inside the workspace only).")
        target = (WORKSPACE / args[1]).resolve()
        if target.parent != WORKSPACE.resolve() or not target.is_file():
            raise ValueError("cat can read only an existing file directly inside the workspace.")
        args[1] = str(target)
    if args[0] == "ls":
        if len(args) == 1:
            args.append(str(WORKSPACE))
        elif len(args) == 2:
            target = Path(args[1])
            if target.is_absolute():
                resolved = target.resolve()
            else:
                resolved = (WORKSPACE / target).resolve()
            if resolved != WORKSPACE.resolve() and WORKSPACE.resolve() not in resolved.parents:
                raise ValueError("ls is restricted to the workspace directory.")
            if not resolved.exists():
                raise ValueError("That workspace path does not exist.")
            args[1] = str(resolved)
        else:
            raise ValueError("Usage: ls [workspace-subdirectory].")
    return args


def output_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")[-12000:]


def update_job(job: dict[str, Any]) -> None:
    proc: subprocess.Popen[bytes] = job["process"]
    rc = proc.poll()
    if rc is not None and job["status"] in {"RUNNING", "STOPPING"}:
        previous_status = job["status"]
        job["status"] = "STOPPED" if previous_status == "STOPPING" else ("COMPLETED" if rc == 0 else "FAILED")
        job["return_code"] = rc
        try:
            out, err = proc.communicate(timeout=0.1)
        except subprocess.TimeoutExpired:
            out, err = b"", b""
        job["stdout"] = output_text(out)
        job["stderr"] = output_text(err)
        job["finished_at"] = datetime.now(timezone.utc).isoformat()
        audit("job_finished", job_id=job["id"], pid=job["pid"], return_code=rc)


def public_job(job: dict[str, Any]) -> dict[str, Any]:
    update_job(job)
    return {
        "id": job["id"],
        "pid": job["pid"],
        "command": job["command"],
        "status": job["status"],
        "started_at": job["started_at"],
        "finished_at": job.get("finished_at"),
        "return_code": job.get("return_code"),
        "stdout": job.get("stdout", ""),
        "stderr": job.get("stderr", ""),
        "background": job["background"],
    }


def spawn(args: list[str], raw: str, background: bool) -> dict[str, Any]:
    global next_job_id
    cwd = str(WORKSPACE) if args[0] in {"ls", "cat"} else str(ROOT)
    started = datetime.now(timezone.utc).isoformat()
    # No shell=True; process is started directly with a validated argv list.
    proc = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    with lock:
        jid = next_job_id
        next_job_id += 1
        job = {
            "id": jid,
            "pid": proc.pid,
            "command": raw,
            "process": proc,
            "status": "RUNNING",
            "started_at": started,
            "stdout": "",
            "stderr": "",
            "background": background,
        }
        jobs[jid] = job
    audit("job_started", job_id=jid, pid=proc.pid, command=raw, background=background)
    return job


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:filename>")
def static_files(filename: str):
    if filename in {"app.js", "style.css"}:
        return send_from_directory(FRONTEND, filename)
    return jsonify({"error": "Not found"}), 404


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "mini-linux-shell-api", "platform": os.name})


@app.get("/api/help")
def help_text():
    return jsonify({
        "commands": sorted(ALLOWED),
        "notes": [
            "Commands are executed without a shell.",
            "Pipes, redirects, command chaining, and arbitrary commands are blocked.",
            "ls and cat are restricted to the project workspace.",
            "sleep is limited to 300 seconds.",
        ],
    })


@app.post("/api/execute")
def execute():
    body = request.get_json(silent=True) or {}
    raw = body.get("command", "")
    background = bool(body.get("background", False))
    try:
        args = parse_command(raw)
    except ValueError as exc:
        audit("command_rejected", command=str(raw)[:MAX_COMMAND_LENGTH], reason=str(exc))
        return jsonify({"ok": False, "error": str(exc)}), 400

    try:
        job = spawn(args, raw, background)
        if background:
            return jsonify({"ok": True, "job": public_job(job)}), 201
        proc = job["process"]
        try:
            out, err = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                out, err = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                out, err = proc.communicate()
            job["status"] = "TIMED_OUT"
            job["return_code"] = proc.returncode
            job["stdout"] = output_text(out)
            job["stderr"] = output_text(err)
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            audit("foreground_timeout", job_id=job["id"], pid=job["pid"])
            return jsonify({"ok": True, "job": public_job(job), "timed_out": True})
        job["stdout"] = output_text(out)
        job["stderr"] = output_text(err)
        job["return_code"] = proc.returncode
        job["status"] = "COMPLETED" if proc.returncode == 0 else "FAILED"
        job["finished_at"] = datetime.now(timezone.utc).isoformat()
        audit("foreground_finished", job_id=job["id"], pid=job["pid"], return_code=proc.returncode)
        return jsonify({"ok": True, "job": public_job(job)})
    except OSError as exc:
        audit("spawn_error", command=raw, reason=str(exc))
        return jsonify({"ok": False, "error": f"Could not start process: {exc}"}), 500


@app.get("/api/jobs")
def list_jobs():
    with lock:
        return jsonify({"ok": True, "jobs": [public_job(j) for j in sorted(jobs.values(), key=lambda x: x["id"], reverse=True)]})


@app.post("/api/jobs/<int:job_id>/stop")
def stop_job(job_id: int):
    with lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Unknown job ID."}), 404
        update_job(job)
        if job["status"] != "RUNNING":
            return jsonify({"ok": False, "error": f"Job is already {job['status'].lower()}."}), 409
        proc = job["process"]
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            update_job(job)
            return jsonify({"ok": False, "error": "Process has already exited."}), 409
        job["status"] = "STOPPING"
        audit("job_stop_requested", job_id=job_id, pid=job["pid"])
        return jsonify({"ok": True, "job": public_job(job)})


@app.get("/api/logs")
def logs():
    if not AUDIT_LOG.exists():
        return jsonify({"ok": True, "lines": []})
    lines = AUDIT_LOG.read_text(encoding="utf-8").splitlines()[-100:]
    return jsonify({"ok": True, "lines": lines})


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    print("Mini Linux Shell dashboard: http://127.0.0.1:5000")
    print("Keep this development server local; do not expose it to untrusted networks.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
