@echo off
TITLE J.A.R.V.I.S - Installation Automatique (www.techenclair.fr)
COLOR 0A
cd /d "%~dp0"

echo ======================================================
echo           INSTALLATION DE J.A.R.V.I.S
echo           Site : www.techenclair.fr
echo ======================================================
echo.

:: 1. Python 3.12
set "PYTHON_CMD="
where python >nul 2>&1
if %errorlevel% equ 0 (set "PYTHON_CMD=python")
if "%PYTHON_CMD%"=="" (
    echo [SYSTEME] Python 3.12 manquant. Telechargement...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python_312_installer.exe'"
    start /wait python_312_installer.exe
    del python_312_installer.exe
    pause && exit /b
)

:: 2. Node.js
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [SYSTEME] Node.js manquant. Telechargement...
    powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi' -OutFile 'node_installer.msi'"
    start /wait node_installer.msi
    del node_installer.msi
)

:: 3. Venv
if not exist "venv" (
    echo [SYSTEME] Preparation de l'environnement virtuel...
    "%PYTHON_CMD%" -m venv venv
)

:: 4. Installation de TOUS les modules possibles pour eviter les erreurs
echo [SYSTEME] Installation des composants IA, Audio et Reseau...
".\venv\Scripts\python.exe" -m pip install --upgrade pip
".\venv\Scripts\python.exe" -m pip install python-dotenv google-generativeai groq flask flask-cors requests pygame openai websockets pyaudio SpeechRecognition colorama

if exist "requirements.txt" (
    ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
)

:: 5. Interface Web
where npm >nul 2>&1
if %errorlevel% equ 0 (
    if exist "frontend\package.json" (
        echo [SYSTEME] Installation de l'interface Web...
        cd frontend && call npm install && cd ..
    )
)

:: 6. Creation du demarreur
(
echo @echo off
echo TITLE J.A.R.V.I.S - www.techenclair.fr
echo COLOR 0B
echo cd /d "%%~dp0"
echo ".\venv\Scripts\python.exe" "main2.py"
echo pause
) > "DEMARRER_JARVIS.bat"

echo.
echo ======================================================
echo           INSTALLATION TERMINEE !
echo ======================================================
echo.
echo IMPORTANT POUR TON AMI :
echo 1. Ouvre le fichier '.env' avec le bloc-notes.
echo 2. Ajoute tes cles API (Gemini, OpenAI, etc.).
echo 3. Lance 'DEMARRER_JARVIS.bat'.
echo.
echo Retrouve nous sur www.techenclair.fr
echo ======================================================
pause
