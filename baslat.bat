@echo off
cd /d "%~dp0"
for /f "delims=" %%P in ('py -c "import os,sys; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))"') do set "PYTHONW=%%P"
if not exist "%PYTHONW%" (
    echo Pythonw.exe bulunamadi. Python kurulumunu kontrol edin.
    pause
    exit /b 1
)
start "" "%PYTHONW%" "%~dp0app.py"
