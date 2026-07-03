$ErrorActionPreference = "Stop"

$composeFile = Join-Path $PSScriptRoot "..\infra\docker\docker-compose.yml"

Write-Host "=== RAG Knowledge Base - Local Setup ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Starting services..." -ForegroundColor Yellow
docker compose -f $composeFile up -d --build

Write-Host ""
Write-Host "[2/3] Waiting for backend to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "Backend is ready!" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Write-Host "  Waiting... ($attempt/$maxAttempts)"
        Start-Sleep -Seconds 2
    }
}

if (-not $backendReady) {
    Write-Warning "Backend may not be fully ready yet. Check logs with: docker compose -f $composeFile logs -f backend"
}

Write-Host ""
Write-Host "[3/3] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "=== Service URLs ===" -ForegroundColor Cyan
Write-Host "  API Docs:   http://localhost:8000/docs"
Write-Host "  API Base:   http://localhost:8000/api/v1"
Write-Host "  Frontend:   http://localhost:3000"
Write-Host "  MinIO:      http://localhost:9001 (user: minio, pass: minio12345)"
Write-Host ""
Write-Host "=== Default Admin ===" -ForegroundColor Cyan
Write-Host "  Email:      admin@example.com"
Write-Host "  Password:   Admin123!"
Write-Host ""
Write-Host "=== Useful Commands ===" -ForegroundColor Cyan
Write-Host "  View logs:  docker compose -f $composeFile logs -f"
Write-Host "  Stop:       docker compose -f $composeFile down"
Write-Host "  Restart:    docker compose -f $composeFile restart"
Write-Host ""
