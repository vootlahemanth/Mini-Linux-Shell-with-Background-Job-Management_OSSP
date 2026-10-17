# Mini Linux Shell with Background Job Management

A hackathon-ready Linux process-management demo with:
- A C/POSIX mini shell (`fork`, `execvp`, `waitpid`, signals).
- A responsive browser dashboard.
- A Flask API that safely manages an allowlisted set of Linux commands and background jobs.
- Job listing, stop/terminate controls, command history, output capture, and audit log.
- Automated API tests and documentation.

> **Safety model:** This project intentionally does not provide unrestricted arbitrary command execution through the web UI. The web API accepts only a documented allowlist and runs commands without a shell. Use a dedicated Linux/Ubuntu or WSL environment. Do not expose the Flask server to an untrusted network.

## Architecture

```text
Browser UI (HTML/CSS/JS)
        | HTTP / JSON
        v
Flask API (backend/app.py) ---- audit log (data/audit.log)
        | subprocess.Popen (allowlisted argv; no shell=True)
        v
Linux processes / jobs

C/POSIX mini shell (src/mini_shell.c)
        fork -> execvp -> waitpid / background job table
```

The dashboard backend and the standalone C shell are both functional components. The dashboard uses the same Linux process concepts and provides real process/job controls; the C shell is an independent command-line implementation for demonstrating the required POSIX calls.

## Requirements

- Linux, Ubuntu, or WSL2 with Ubuntu (recommended)
- Python 3.10+
- GCC and Make
- Flask (install with `pip install -r requirements.txt`)

## Quick start (Ubuntu / WSL2)

```bash
sudo apt update
sudo apt install -y build-essential python3 python3-venv
cd mini-linux-shell-hackathon
make
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/app.py
```

Open `http://127.0.0.1:5000` in your browser.

If Flask is missing, install dependencies inside the virtual environment. Keep the server bound to `127.0.0.1` for the demonstration.

## Run the C shell

```bash
make
./mini_shell
```

Supported commands in the C shell: `help`, `jobs`, `pwd`, `date`, `whoami`, `ls`, `echo`, `sleep`, `cd`, `exit`, and `quit`. Add `&` to run a supported external command in the background, e.g. `sleep 30 &`. Use `jobs` to list jobs and `kill JOB_ID` to terminate a job by mini-shell job ID. The C shell is a small teaching shell, not a POSIX-complete shell.

## Dashboard commands

Supported commands: `pwd`, `date`, `whoami`, `hostname`, `ls`, `echo`, `sleep`, `uptime`, `uname`, `cat`, and `help`.
- Enter `sleep 60` and choose **Run in background** to create a background job.
- Use **Jobs** to refresh the process table.
- Select **Stop** to terminate a running job.
- `cat` is restricted to files inside the project `workspace/` directory. Create demo files there if needed.
- `ls` is scoped to the workspace directory.
- Arguments are parsed as simple whitespace-separated tokens; shell operators, pipes, redirection, and command chaining are not supported by the dashboard.

## Safety and implementation notes

- The web API does not use `shell=True`; commands are executed as argument arrays.
- Only allowlisted commands are accepted by the API.
- `cat` and `ls` are restricted to the project workspace.
- Job termination only targets PIDs started and tracked by this application.
- The Flask development server is for a local demo, not production deployment.
- The app does not attempt to kill arbitrary system processes.
- Run as a normal user, not root.

## Tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Tests cover command validation, job listing, foreground execution, background execution, and stopping a tracked job. A few tests can be skipped or behave differently on non-Linux operating systems.

## Repository structure

```text
mini-linux-shell-hackathon/
├── backend/app.py
├── frontend/index.html
├── frontend/style.css
├── frontend/app.js
├── src/mini_shell.c
├── Makefile
├── requirements.txt
├── tests/test_api.py
├── docs/ARCHITECTURE.md
├── docs/PROJECT_REPORT.md
├── docs/TEST_PLAN.md
├── docs/PRESENTATION_OUTLINE.md
├── scripts/run.sh
├── workspace/                 # safe sample files for cat/ls
└── data/                      # generated logs (created on first run)
```

## Demo script (2–3 minutes)

1. Start the app and show the dashboard.
2. Run `pwd`, `date`, and `whoami` in the terminal panel.
3. Run `sleep 60` in the background.
4. Refresh Jobs and point out the job ID, PID, command, and status.
5. Stop the job and refresh the table.
6. Try `invalid_command_xyz` and show safe validation.
7. Open the C shell in a terminal, run `sleep 20 &`, `jobs`, and `kill 1`.

## Team contributions (edit before submission)

Replace the placeholders with actual team members and IDs. Ensure every member makes a meaningful commit under their own GitHub account.

- Member 1: UI/dashboard and demo
- Member 2: C/POSIX shell engine
- Member 3: Flask API, process/job lifecycle, and tests
- Member 4 (if applicable): documentation, validation, presentation

## Submission checklist

- [ ] Replace team/supervisor placeholders in report and presentation.
- [ ] Run the project from a clean checkout.
- [ ] Run all tests and capture genuine screenshots of your own running app.
- [ ] Add your team names/IDs and supervisor's name.
- [ ] Push source code and documentation to GitHub.
- [ ] Do not claim unperformed tests or features.
