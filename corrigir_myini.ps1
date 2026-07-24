$path = "C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"

# Ler bytes e remover BOM UTF-8 (EF BB BF)
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $bytes = $bytes[3..($bytes.Length - 1)]
    [System.IO.File]::WriteAllBytes($path, $bytes)
    Write-Host "[OK] BOM removido do my.ini" -ForegroundColor Green
} else {
    Write-Host "my.ini ja esta correto (sem BOM)" -ForegroundColor Yellow
}

Write-Host "Iniciando MySQL..." -ForegroundColor Cyan
Start-Process "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" -ArgumentList "--defaults-file=`"C:\ProgramData\MySQL\MySQL Server 8.0\my.ini`"", "--console" -WindowStyle Normal

Start-Sleep 8
$port = netstat -an | Select-String ":3306"
if ($port) {
    Write-Host "[OK] MySQL rodando na porta 3306!" -ForegroundColor Green
    Write-Host $port
} else {
    Write-Host "[ERRO] MySQL nao iniciou" -ForegroundColor Red
}
Read-Host "Pressione Enter para fechar"
