const $ = (id) => document.getElementById(id);
const output = $("terminalOutput");
let toastTimer;

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3000);
}
function addTerminalLine(text, cls = "output-line") {
  const div = document.createElement("div");
  div.className = `terminal-line ${cls}`;
  div.textContent = text;
  output.appendChild(div);
  output.scrollTop = output.scrollHeight;
}
function clearTerminal() {
  output.replaceChildren();
}
function timeLabel(value) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleTimeString();
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}
async function health() {
  try {
    await api("/api/health");
    $("healthText").textContent = "Connected";
  } catch {
    $("healthText").textContent = "Unavailable";
  }
}
async function runCommand(command, background) {
  if (!command.trim()) return;
  addTerminalLine(`hemanth@minishell:~$ ${command}${background ? "  [background]" : ""}`, "command-line");
  $("commandInput").value = "";
  try {
    const data = await api("/api/execute", {method:"POST", body:JSON.stringify({command, background})});
    const job = data.job;
    if (background) {
      addTerminalLine(`[job ${job.id}] started with PID ${job.pid}`);
      toast(`Background job ${job.id} started.`);
    } else {
      if (job.stdout) addTerminalLine(job.stdout.trimEnd());
      if (job.stderr) addTerminalLine(job.stderr.trimEnd(), "error-line");
      addTerminalLine(`[${job.status}] exit code ${job.return_code}`);
    }
    await refreshAll();
  } catch (err) {
    addTerminalLine(`Error: ${err.message}`, "error-line");
    toast(err.message);
  }
}
async function refreshJobs() {
  const data = await api("/api/jobs");
  const jobs = data.jobs;
  $("metricTotal").textContent = jobs.length;
  $("metricRunning").textContent = jobs.filter(j => ["RUNNING","STOPPING"].includes(j.status)).length;
  $("metricCompleted").textContent = jobs.filter(j => ["COMPLETED","FAILED","TIMED_OUT"].includes(j.status)).length;
  const body = $("jobsBody");
  body.replaceChildren();
  if (!jobs.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 6; td.className = "empty"; td.textContent = "No jobs yet. Start one from Terminal.";
    tr.appendChild(td); body.appendChild(tr); return;
  }
  for (const job of jobs) {
    const tr = document.createElement("tr");
    const values = [
      `#${job.id}`, job.command, job.pid, job.status, timeLabel(job.started_at)
    ];
    values.forEach((value, i) => {
      const td = document.createElement("td");
      td.textContent = value;
      if (i === 1) td.className = "command-cell";
      if (i === 3) {
        const badge = document.createElement("span");
        badge.className = `status ${job.status}`;
        badge.textContent = job.status;
        td.replaceChildren(badge);
      }
      tr.appendChild(td);
    });
    const action = document.createElement("td");
    const button = document.createElement("button");
    button.className = "stop-button";
    button.textContent = "Stop";
    button.disabled = !["RUNNING","STOPPING"].includes(job.status);
    button.addEventListener("click", () => stopJob(job.id));
    action.appendChild(button); tr.appendChild(action);
    body.appendChild(tr);
  }
}
async function stopJob(id) {
  if (!confirm(`Send SIGTERM to tracked job #${id}?`)) return;
  try {
    await api(`/api/jobs/${id}/stop`, {method:"POST", body:"{}"});
    toast(`Stop requested for job #${id}.`);
    await refreshAll();
  } catch (err) { toast(err.message); }
}
async function refreshLogs() {
  const data = await api("/api/logs");
  const list = $("logList");
  list.replaceChildren();
  if (!data.lines.length) {
    const empty = document.createElement("div"); empty.className = "empty"; empty.textContent = "No activity recorded yet.";
    list.appendChild(empty); return;
  }
  for (const line of data.lines.slice().reverse()) {
    const entry = document.createElement("div"); entry.className = "log-entry";
    const pre = document.createElement("pre"); pre.textContent = line;
    entry.appendChild(pre); list.appendChild(entry);
  }
}
async function refreshAll() {
  try { await refreshJobs(); } catch (err) { toast(err.message); }
}
document.querySelectorAll(".nav-item").forEach(button => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b === button));
    const panel = button.dataset.panel;
    $("terminalPanel").classList.toggle("hidden", panel !== "terminal");
    $("jobsPanel").classList.toggle("hidden", panel !== "jobs");
    $("activityPanel").classList.toggle("hidden", panel !== "activity");
    $("pageTitle").textContent = {terminal:"Terminal",jobs:"Background jobs",activity:"Activity log"}[panel];
    if (panel === "jobs") await refreshAll();
    if (panel === "activity") await refreshLogs();
  });
});
$("commandForm").addEventListener("submit", event => {
  event.preventDefault();
  runCommand($("commandInput").value, $("backgroundToggle").checked);
});
document.querySelectorAll("[data-command]").forEach(button => button.addEventListener("click", () => {
  $("commandInput").value = button.dataset.command;
  $("commandInput").focus();
}));
$("clearBtn").addEventListener("click", clearTerminal);
$("refreshBtn").addEventListener("click", refreshAll);
$("jobsRefresh").addEventListener("click", refreshAll);
$("logsRefresh").addEventListener("click", refreshLogs);
document.addEventListener("keydown", event => {
  if (event.ctrlKey && event.key.toLowerCase() === "l") { event.preventDefault(); clearTerminal(); }
});
health();
refreshAll();
setInterval(refreshAll, 5000);
