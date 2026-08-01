Set objShell = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.ShellExecute "cmd.exe", "/c """ & pasta & "\INICIAR_JP_DOCES.bat" & """", "", "runas", 1
