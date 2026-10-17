# Test Plan

Run from the repository root with the Flask dependency installed:

```bash
python -m unittest discover -s tests -v
```

| ID | Scenario | Input/action | Expected result |
|---|---|---|---|
| T01 | Health endpoint | `GET /api/health` | HTTP 200, `ok: true` |
| T02 | Foreground command | `pwd` | Output captured; completed status |
| T03 | Background job | `sleep 20`, background=true | Job ID/PID returned promptly |
| T04 | Job listing | `GET /api/jobs` | New job appears |
| T05 | Stop tracked job | `POST /api/jobs/<id>/stop` | SIGTERM requested |
| T06 | Unsupported command | `invalid_command_xyz` | HTTP 400, safe error |
| T07 | Shell operator | `pwd; whoami` | HTTP 400, operator rejected |
| T08 | Workspace file read | `cat sample.txt` | File content returned |
| T09 | Path traversal | `cat ../README.md` | HTTP 400, path rejected |
| T10 | Help endpoint | `GET /api/help` | Allowed commands returned |

## Test report template

Fill this table with actual outcomes during the final rehearsal.

| Test ID | Actual result | Pass/Fail | Evidence |
|---|---|---|---|
| T01–T10 | [Complete after running] | [Complete after running] | [Screenshot/log] |
