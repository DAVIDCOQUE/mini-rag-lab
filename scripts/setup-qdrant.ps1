# Descarga el binario de Qdrant y el dashboard web.
# Idempotente: si ya existen, no vuelve a descargar.
$ErrorActionPreference = 'Stop'

$QdrantVersion = 'v1.18.2'
$WebUiVersion  = 'v0.2.15'

$Root   = Split-Path -Parent $PSScriptRoot
$Target = Join-Path $Root 'qdrant-x86_64-pc-windows-msvc'
$Exe    = Join-Path $Target 'qdrant.exe'
$Static = Join-Path $Target 'static'
$Tmp    = Join-Path $env:TEMP "qdrant-setup-$QdrantVersion"

New-Item -ItemType Directory -Force -Path $Target, $Tmp | Out-Null

if (Test-Path $Exe) {
    Write-Host "qdrant.exe ya existe, se omite la descarga."
} else {
    $zip = Join-Path $Tmp 'qdrant.zip'
    Write-Host "Descargando Qdrant $QdrantVersion (~27 MB)..."
    Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/download/$QdrantVersion/qdrant-x86_64-pc-windows-msvc.zip" -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $Tmp -Force
    $found = Get-ChildItem -Path $Tmp -Filter 'qdrant.exe' -Recurse | Select-Object -First 1
    if (-not $found) { throw "El zip de Qdrant no contiene qdrant.exe." }
    Copy-Item $found.FullName -Destination $Exe
}

if (Test-Path $Static) {
    Write-Host "Dashboard ya existe, se omite la descarga."
} else {
    $zip = Join-Path $Tmp 'dist-qdrant.zip'
    Write-Host "Descargando dashboard $WebUiVersion (~7 MB)..."
    Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant-web-ui/releases/download/$WebUiVersion/dist-qdrant.zip" -OutFile $zip
    $unpack = Join-Path $Tmp 'webui'
    Expand-Archive -Path $zip -DestinationPath $unpack -Force
    # Qdrant sirve el dashboard desde ./static; el zip trae la carpeta como 'dist' o 'static'
    $dist = Get-ChildItem -Path $unpack -Directory | Where-Object { $_.Name -in 'dist', 'static' } | Select-Object -First 1
    if ($dist) { Move-Item $dist.FullName $Static } else { Move-Item $unpack $Static }
}

Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Listo. Arranca Qdrant con:"
Write-Host "  .\qdrant-x86_64-pc-windows-msvc\qdrant.exe"
Write-Host "  REST:      http://localhost:6333"
Write-Host "  Dashboard: http://localhost:6333/dashboard"
