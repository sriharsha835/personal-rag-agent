@"
# Troubleshooting (Windows / PowerShell)

- **Activate venv:** run `.venv\Scripts\Activate.ps1` with no `source`. If blocked: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
- **Use `python`, not `python3`:** `python3` points at a different Python without the venv's packages.
- **Use `127.0.0.1`, not `localhost`:** another Postgres/WSL relay can answer on localhost. Applies to the DB (127.0.0.1:55432) and the API (http://127.0.0.1:8000).
- **No `<` redirect in PowerShell:** use `Get-Content file.sql | docker exec -i ...` instead.
- **`curl` is an alias in PowerShell:** use `curl.exe` or `Invoke-RestMethod` for POST requests.
- **"No matching distribution" / needs Rust or MSVC:** the pinned package has no wheel for Python 3.14. Bump the pin to a newer version instead of installing compilers.
- **Use `docker exec -i`, not `-it`,** in the VS Code terminal if TTY errors appear.
- **Port conflicts:** check with `netstat -ano | findstr :<port>` and `tasklist /FI "PID eq <pid>"`.
- **Running the API:** uvicorn occupies its terminal; run test commands in a second terminal.
"@