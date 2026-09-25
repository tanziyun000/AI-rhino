Remove-Item 'D:\Ai+rhino\check_netease.ps1' -ErrorAction SilentlyContinue
Start-Process -FilePath 'D:\Minecraft\MC_setup.exe' -WorkingDirectory 'D:\Minecraft'
Start-Sleep -Seconds 3
$p = Get-Process -Name 'MC_setup' -ErrorAction SilentlyContinue
if ($p) {
    Write-Host "Installer started OK, PID: $($p.Id)"
} else {
    Write-Host 'Installer exited immediately - possible antivirus block or SmartScreen intercept'
}
