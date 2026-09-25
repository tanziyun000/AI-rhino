Write-Host '=== Installer still running? ==='
$proc = Get-Process -Name 'MC_setup' -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Yes - PID: $($proc.Id), Started: $($proc.StartTime)"
} else {
    Write-Host 'No (installer not currently running)'
}

Write-Host ''
Write-Host '=== D:\Minecraft contents ==='
if (Test-Path 'D:\Minecraft') {
    Get-ChildItem 'D:\Minecraft' -Force | ForEach-Object {
        if ($_.PSIsContainer) {
            Write-Host "  [DIR]    $($_.Name)"
        } else {
            $mb = [math]::Round($_.Length / 1MB, 2)
            Write-Host "  [$mb MB]  $($_.Name)"
        }
    }
} else {
    Write-Host '  (D:\Minecraft does not exist)'
}

Write-Host ''
Write-Host '=== Search for installed Minecraft elsewhere ==='
$paths = @('C:\Program Files\Minecraft', 'C:\Program Files (x86)\Minecraft',
           'C:\Program Files\Minecraft Launcher', 'C:\Program Files (x86)\Minecraft Launcher',
           'C:\Program Files\NetEase', 'C:\Program Files (x86)\NetEase',
           'C:\Program Files (x86)\网易我的世界', 'C:\Program Files\网易我的世界',
           "$env:LOCALAPPDATA\NetEase", "$env:LOCALAPPDATA\Minecraft",
           "$env:LOCALAPPDATA\Kingsoft\NetEase")
foreach ($p in $paths) {
    if (Test-Path $p) { Write-Host "  FOUND: $p" }
}

Write-Host ''
Write-Host '=== Desktop shortcuts mentioning Minecraft ==='
$desktops = @("$env:USERPROFILE\Desktop", "$env:USERPROFILE\OneDrive\Desktop", 'C:\Users\Public\Desktop')
foreach ($d in $desktops) {
    if (Test-Path $d) {
        Get-ChildItem $d -Filter '*.lnk' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Minecraft|我的世界|MC' } | ForEach-Object { Write-Host "  $($_.FullName)" }
    }
}

Write-Host ''
Write-Host '=== Start Menu shortcuts ==='
$sms = @("$env:APPDATA\Microsoft\Windows\Start Menu\Programs", 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs')
foreach ($s in $sms) {
    if (Test-Path $s) {
        Get-ChildItem $s -Recurse -Filter '*.lnk' -ErrorAction SilentlyContinue -Depth 3 | Where-Object { $_.Name -match 'Minecraft|我的世界|MC' } | ForEach-Object { Write-Host "  $($_.FullName)" }
    }
}

Write-Host ''
Write-Host '=== Registry uninstall entries ==='
$regPaths = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
              'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
              'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')
foreach ($rp in $regPaths) {
    Get-ItemProperty $rp -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'Minecraft|我的世界' } | ForEach-Object {
        Write-Host "  $($_.DisplayName) | $($_.InstallLocation) | Uninstall: $($_.UninstallString)"
    }
}

Write-Host ''
Write-Host '=== Downloads folder ==='
$dl = "$env:USERPROFILE\Downloads"
if (Test-Path $dl) {
    Get-ChildItem $dl -Filter 'MC_setup*' -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $($_.FullName) ($([math]::Round($_.Length/1MB,2)) MB)" }
}
