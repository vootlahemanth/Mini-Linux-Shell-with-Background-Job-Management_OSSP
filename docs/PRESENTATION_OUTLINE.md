# Presentation Outline (8 slides)

1. **Title** — Mini Linux Shell with Background Job Management; team names, IDs and supervisor.
2. **Problem statement** — Background work is hard to track for beginners; need command execution and safe process control.
3. **Objectives and features** — Foreground commands, background jobs, job table, termination, output and audit logs.
4. **Architecture** — Browser → Flask API → validated process launch; standalone C shell → POSIX process APIs.
5. **Implementation** — `fork()`, `execvp()`, `waitpid()`, `kill()`, signals; Flask, HTML/CSS/JS.
6. **Live demo** — `pwd`, `date`, background `sleep 60`, inspect PID/job, stop job, invalid command.
7. **Testing, safety and limitations** — allowlist, no `shell=True`, workspace restriction, local-only service, test cases.
8. **Impact and conclusion** — approachable process management, OS learning value, next steps.

Do not present features as tested until the team has verified them on the demo machine.
