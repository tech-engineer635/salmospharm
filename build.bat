@echo off
setlocal

echo.
echo ========================================
echo  Build SALMOSPHARM avec PyInstaller
echo ========================================
echo.

echo Nettoyage des anciens dossiers build et dist...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Generation de l'executable Windows...
pyinstaller app/main.py ^
  --name SALMOSPHARM ^
  --windowed ^
  --onedir ^
  --icon app/assets/logo.ico ^
  --add-data "app/assets;assets" ^
  --hidden-import passlib.handlers.bcrypt

echo.
echo Build termine.
echo L'executable attendu se trouve dans dist\SALMOSPHARM\SALMOSPHARM.exe
echo.
pause

endlocal
