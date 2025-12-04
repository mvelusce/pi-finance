# Troubleshooting PyEnv Issues

If you're using **pyenv** and encountering `ModuleNotFoundError: No module named 'fastapi'` even though it's installed in your virtual environment, this is because pyenv intercepts commands.

## The Issue

When you run `uvicorn app.main:app`, pyenv's shim runs first and uses the global Python instead of your venv's Python, even when the venv is activated.

## Solutions

### ✅ Solution 1: Use `python -m uvicorn` (RECOMMENDED)

```bash
cd /Users/mveluscek/Workspace/personal/pi-finance
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

This explicitly uses the venv's Python and is the recommended approach.

### ✅ Solution 2: Use the startup script

```bash
./run_server.sh
```

This script is included in the repo and handles the pyenv issue automatically.

### Alternative: Use absolute path

```bash
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Managing Server Processes

### Stop the server

If you get "Address already in use" error:

```bash
# Kill all processes using port 8000
kill -9 $(lsof -ti:8000)

# Or kill all uvicorn processes
pkill -f "uvicorn app.main:app"
```

### Check if server is running

```bash
# Check port 8000
lsof -ti:8000

# Test API
curl http://localhost:8000/health
```

### View server logs (if running in background)

```bash
# If started with: python -m uvicorn app.main:app > api.log 2>&1 &
tail -f api.log
```

## Why This Happens

1. **pyenv shims** intercept commands in your PATH
2. Even with venv activated, `uvicorn` command uses pyenv's Python
3. pyenv's Python doesn't have access to venv's packages
4. Solution: Use `python -m` which directly uses venv's Python

## Prevention

Always use `python -m` when running Python modules in a venv with pyenv:

```bash
# ✅ Good
python -m uvicorn app.main:app --reload
python -m pip install package
python -m pytest

# ❌ May fail with pyenv
uvicorn app.main:app --reload
pip install package
pytest
```

