Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "cmd.exe", "/c """ & "C:\PROJETOS\SIS_JP_doces\INICIAR_JP_DOCES.bat" & """", "", "runas", 1
