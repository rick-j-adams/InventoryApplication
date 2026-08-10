@echo off
setlocal enabledelayedexpansion

REM Create a virtual environment if it does not exist
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv "%~dp0.venv"
) else (
    echo Virtual environment already exists.
)

call "%~dp0.venv\Scripts\activate"

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

echo Setting database environment variables...
set "DATABASE_URL=sqlite:///%~dp0inventory.db"
set "SECRET_KEY=change_this_secret"
set "FLASK_APP=app.py"

echo Initializing database and creating admin_user...
python -m flask init-db

echo Launching Flask inventory app...
python "%~dp0app.py"

endlocal
