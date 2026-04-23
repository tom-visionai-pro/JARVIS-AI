@echo off
TITLE J.A.R.V.I.S — Système Assistant
COLOR 0B
cd /d "%~dp0"

echo ======================================================
echo           INITIALISATION DE J.A.R.V.I.S
echo ======================================================
echo.
echo [SYSTEME] Chargement de l'environnement Python...
echo [SYSTEME] Activation du serveur Web et de l'IA...
echo.

:: Utilisation du chemin absolu pour Python et relatif pour le script
"c:\Users\ASUS TUF\Desktop\MON_JARVIS\.venv-1\Scripts\python.exe" "main2.py"

echo.
echo [INFO] JARVIS s'est arrete.
pause
