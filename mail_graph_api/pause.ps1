Write-Host "Plugin update required. Please update the Odoo plugin now."
Write-Host "Press 'y' or Enter to continue once you've updated the plugin..." -ForegroundColor Yellow
$response = Read-Host

while ($response -ne 'y' -and $response -ne '') {
    Write-Host "Please press 'y' or Enter to continue..." -ForegroundColor Yellow
    $response = Read-Host
}

Write-Host "Continuing execution..." -ForegroundColor Green

# Display error.md content if it exists
if (Test-Path "error.md") {
    Write-Host "`nLatest Error:" -ForegroundColor Red
    Get-Content "error.md" | ForEach-Object { Write-Host $_ }
} 