@echo off
echo Abrindo o Chrome com o perfil do Bot...
echo.
echo 1. Faça o login no Instagram e no TikTok calmamente.
echo 2. Feche o navegador quando terminar.
echo 3. Depois, rode sua automacao novamente.
echo.
pause
start chrome.exe --user-data-dir="%~dp0perfil_chrome_bot"
exit
