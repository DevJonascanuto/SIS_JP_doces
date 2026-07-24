$log = 'C:\PROJETOS\SIS_JP_doces\fix_account_log.txt'
"Alterando conta do servico MySQL80 para LocalSystem via registro..." | Out-File $log

# Alterar via registro diretamente
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\MySQL80"
Set-ItemProperty -Path $regPath -Name "ObjectName" -Value "LocalSystem"
"ObjectName alterado para LocalSystem" | Out-File -Append $log

# Verificar
$val = Get-ItemProperty -Path $regPath -Name "ObjectName"
"Valor atual: $($val.ObjectName)" | Out-File -Append $log

# Iniciar servico
"Iniciando MySQL80..." | Out-File -Append $log
Start-Service MySQL80 -ErrorAction SilentlyContinue
Start-Sleep -Seconds 8

$status = (Get-Service MySQL80).Status
"Status: $status" | Out-File -Append $log

if ($status -eq "Running") {
    Write-Host "[OK] MySQL80 rodando com sucesso!" -ForegroundColor Green
    netstat -an | findstr ":3306" | Out-File -Append $log
} else {
    Write-Host "[ERRO] Falha. Verificando log do MySQL..." -ForegroundColor Red
    $hostname = $env:COMPUTERNAME
    Get-Content "C:\ProgramData\MySQL\MySQL Server 8.0\Data\$hostname.err" -Tail 15 | Out-File -Append $log
    Write-Host "Verifique: C:\PROJETOS\SIS_JP_doces\fix_account_log.txt"
}

Read-Host "Pressione Enter para fechar"
