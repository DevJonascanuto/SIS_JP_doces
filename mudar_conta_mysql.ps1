Write-Host "=== Configurar MySQL para rodar como usuario jonas ===" -ForegroundColor Cyan
Write-Host ""
$senha = Read-Host "Digite sua senha do Windows" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($senha)
$senhaTexto = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

Write-Host "Configurando servico MySQL80 para rodar como .\jonas..." -ForegroundColor Yellow
$resultado = sc.exe config MySQL80 obj= ".\jonas" password= $senhaTexto
Write-Host $resultado

Write-Host "Iniciando servico MySQL80..." -ForegroundColor Yellow
net start MySQL80

Start-Sleep -Seconds 5
$status = (Get-Service MySQL80).Status
if ($status -eq "Running") {
    Write-Host "`n[OK] MySQL80 iniciado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "`n[ERRO] Falha ao iniciar. Status: $status" -ForegroundColor Red
}
Write-Host ""
Read-Host "Pressione Enter para fechar"
