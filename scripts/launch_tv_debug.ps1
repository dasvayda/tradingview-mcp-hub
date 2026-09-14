# Launch TradingView Desktop with Chrome DevTools Protocol on port 9222.
# Closes existing TradingView.exe first. Store/MSIX installs may still block CDP.

param(
    [int]$Port = 9222
)

$ErrorActionPreference = "Stop"
Write-Host "Closing existing TradingView..."
Get-Process TradingView -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

$tvExe = $null
$candidates = @(
    (Join-Path $env:LOCALAPPDATA "TradingView\TradingView.exe"),
    (Join-Path $env:ProgramFiles "TradingView\TradingView.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "TradingView\TradingView.exe")
)
foreach ($path in $candidates) {
    if ($path -and (Test-Path $path)) { $tvExe = $path; break }
}

if (-not $tvExe) {
    $pkg = Get-AppxPackage -Name "TradingView.Desktop" -ErrorAction SilentlyContinue
    if ($pkg -and (Test-Path (Join-Path $pkg.InstallLocation "TradingView.exe"))) {
        $tvExe = Join-Path $pkg.InstallLocation "TradingView.exe"
    }
}

if (-not $tvExe) {
    Write-Host "TradingView.exe not found. Launch manually:"
    Write-Host "  `"C:\path\to\TradingView.exe`" --remote-debugging-port=$Port"
    exit 1
}

Write-Host "Found: $tvExe"
Write-Host "Starting with --remote-debugging-port=$Port"
Start-Process -FilePath $tvExe -ArgumentList "--remote-debugging-port=$Port"

$ok = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -UseBasicParsing -TimeoutSec 2
        $ok = $true
        break
    } catch {
        Write-Host "Waiting for CDP..."
    }
}

if ($ok) {
    Write-Host "CDP ready at http://127.0.0.1:$Port"
    exit 0
}

Write-Host "TradingView started but CDP did not open on port $Port."
Write-Host "Store/MSIX builds sometimes block the debug port. Use MCP tool tv_launch as a fallback."
exit 1
