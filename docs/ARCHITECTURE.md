# System Architecture

## Components

1. **Web frontend:** HTML/CSS/JavaScript dashboard; calls JSON endpoints with `fetch`.
2. **Flask API:** validates input, rejects shell metacharacters, invokes allowlisted executables as argument arrays, tracks process handles and writes audit records.
3. **C shell:** standalone POSIX shell prototype using `fork`, `execvp`, `waitpid`, `kill`, `SIGTERM`, and a background-job table.
4. **Workspace:** controlled directory for file-oriented commands.
5. **Audit log:** newline-delimited JSON events under `data/audit.log`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/api/health` | Health check |
| GET | `/api/help` | Allowed commands and restrictions |
| POST | `/api/execute` | Execute a validated command |
| GET | `/api/jobs` | List tracked jobs and statuses |
| POST | `/api/jobs/<id>/stop` | Send SIGTERM to a tracked process group |
| GET | `/api/logs` | Last 100 audit entries |

### Execute request

```json
{"command":"sleep 30","background":true}
```

The server returns a job ID, PID, status, and timestamps. Foreground commands have a 15-second API timeout. Background processes are tracked in memory for the lifetime of the server.

## Process lifecycle

```text
Validate command
      |
      v
Spawn allowlisted argv (no shell)
      |
      +---- foreground ---> wait / capture stdout and stderr
      |
      +---- background ---> return job ID/PID
                                  |
                             poll process status
                                  |
                         Stop -> SIGTERM process group
```

## Design limitations

- This is a learning prototype, not a multi-user production service.
- Job state is in memory and resets on server restart.
- Simple token parsing only; pipes, redirection, environment expansion, and shell scripting are not implemented.
- The dashboard uses Flask's development server bound to loopback.
- The C shell has a separate job table and is run from a terminal.
