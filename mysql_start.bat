@echo off
echo Iniciando MySQL...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --console 2>&1
echo.
echo MySQL encerrou com codigo: %errorlevel%
pause
