# Project Report: Mini Linux Shell with Background Job Management

**Team members:** [Enter names and student IDs]  
**Supervisor:** [Enter supervisor name]  
**Event:** Hackathon — 17 October 2026  
**Project title:** Mini Linux Shell with Background Job Management

## 1. Abstract

This project demonstrates a compact Linux shell and a browser-based process-management dashboard. Users can execute a controlled set of Linux commands, start long-running tasks in the background, inspect job IDs and process IDs, review command results, and request termination of tracked jobs. The C implementation illustrates core POSIX process APIs, while a Flask API and responsive frontend make the concepts easy to demonstrate.

## 2. Problem definition

Traditional command-line workflows can be difficult for beginners to understand, especially when commands run in the background. Users need a simple interface to distinguish foreground execution from background execution, see process identifiers and statuses, and stop jobs without affecting unrelated processes.

## 3. Objectives

- Execute a documented set of Linux commands.
- Demonstrate process creation and program execution using `fork()` and `execvp()`.
- Demonstrate waiting and process status handling with `waitpid()`.
- Support background jobs and list their IDs/PIDs/status.
- Send a termination signal only to jobs started and tracked by the application.
- Provide a responsive web dashboard and an audit trail.
- Validate inputs and restrict file-oriented commands to a workspace.

## 4. Proposed solution

The system has a C/POSIX teaching shell and a Flask-backed web dashboard. The frontend sends JSON requests to the API. The API validates each command against an allowlist and starts processes directly without a command interpreter. It tracks process metadata and writes lifecycle events to an audit log. The C shell separately implements a command loop and background job table.

## 5. Technologies

- C, GCC, Make
- Linux/POSIX APIs: `fork`, `execvp`, `waitpid`, `kill`, signals
- Python 3 and Flask
- HTML, CSS, JavaScript
- JSON, Git and GitHub
- Python `unittest`

## 6. Implementation modules

- `src/mini_shell.c`: command parser, allowlist, foreground execution, background jobs, job listing, termination and cleanup.
- `backend/app.py`: API endpoints, validation, process tracking, output capture and audit logging.
- `frontend/index.html`: dashboard layout.
- `frontend/style.css`: responsive dark interface.
- `frontend/app.js`: API requests, terminal output, job table and activity log.
- `tests/test_api.py`: validation and process lifecycle tests.

## 7. Testing and validation

Run the tests using `python -m unittest discover -s tests -v`. Demonstrate `pwd`, `date`, `whoami`, `ls`, `sleep 30` in background mode, job listing, job termination, and rejection of an unsupported command. Record actual results and attach screenshots captured from the final running build before submission.

## 8. Safety and limitations

The web API uses a strict command allowlist and does not invoke a shell interpreter. File reads are restricted to a file directly inside the project workspace. Job termination targets only process groups started by the app. This is a local educational prototype; it should not run as root or be exposed to untrusted networks. The dashboard's in-memory job table resets after restart.

## 9. Expected impact

The project makes Linux process management more approachable for students, supports live demonstrations of foreground/background execution, and offers a practical starting point for learning process lifecycle management and API-backed system tools.

## 10. Conclusion

The prototype combines a command-line shell implementation with a web dashboard for process control. It demonstrates the key requested features—command execution, background jobs, job listing, and process termination—while including validation, documentation, tests, and a controlled demonstration environment.

## 11. Submission details to complete

- Add team member names and student IDs.
- Add supervisor's name and institution details.
- Add screenshots of the actual running project.
- Add GitHub repository URL.
- Add the real test execution output; do not mark tests as passed until executed.
