@echo off
echo ============================================
echo  Corrigindo permissoes do MySQL80
echo ============================================

echo [1/4] Parando qualquer instancia MySQL em execucao...
net stop MySQL80 2>nul
taskkill /F /IM mysqld.exe 2>nul

echo [2/4] Corrigindo permissoes da pasta de dados...
icacls "C:\ProgramData\MySQL\MySQL Server 8.0\Data" /grant "NT Service\MySQL80:(OI)(CI)F" /T
icacls "C:\ProgramData\MySQL\MySQL Server 8.0\Data" /grant "NETWORK SERVICE:(OI)(CI)F" /T
icacls "C:\ProgramData\MySQL\MySQL Server 8.0\Data" /grant "SYSTEM:(OI)(CI)F" /T

echo [3/4] Removendo atributo somente-leitura dos arquivos...
attrib -R "C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.*" /S

echo [4/4] Iniciando servico MySQL80...
net start MySQL80

echo.
if %errorlevel%==0 (
    echo [OK] MySQL iniciado com sucesso!
) else (
    echo [ERRO] Falha ao iniciar. Verifique o log em:
    echo C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.err
)
echo ============================================
pause
