# Levanta Sara en local, en orden: PostgreSQL -> Ollama -> Qdrant -> backend -> frontend.
# Idempotente: lo que ya responde no se vuelve a arrancar.
# Uso (desde la raiz):  .\scripts\start-sara.ps1            todo
#                       .\scripts\start-sara.ps1 -NoFrontend sin Angular (p. ej. solo Unity)
param(
    [switch]$NoFrontend
)

$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$Backend  = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'
$Python   = Join-Path $Backend '.venv\Scripts\python.exe'
$QdrantDir = Join-Path $Root 'qdrant-x86_64-pc-windows-msvc'

$OllamaUrl  = 'http://127.0.0.1:11434/api/tags'
$QdrantUrl  = 'http://127.0.0.1:6333/healthz'
$BackendUrl = 'http://127.0.0.1:8000/health'
$FrontUrl   = 'http://localhost:4200'

function Test-Url([string]$Url) {
    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-Url([string]$Name, [string]$Url, [int]$TimeoutS) {
    $deadline = (Get-Date).AddSeconds($TimeoutS)
    while ((Get-Date) -lt $deadline) {
        if (Test-Url $Url) { Write-Host "  $Name listo." -ForegroundColor Green; return }
        Start-Sleep -Seconds 2
    }
    throw "$Name no respondio en $TimeoutS s ($Url)."
}

function Step([string]$Text) { Write-Host "`n> $Text" -ForegroundColor Cyan }

# --- 1. PostgreSQL (servicio de Windows) ---
Step 'PostgreSQL'
$pg = Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pg) {
    Write-Warning 'No se encontro un servicio de PostgreSQL. Si corre de otra forma, ignora este aviso.'
} elseif ($pg.Status -ne 'Running') {
    try {
        Start-Service $pg.Name
        Write-Host "  $($pg.Name) iniciado." -ForegroundColor Green
    } catch {
        throw "No se pudo iniciar $($pg.Name). Abre PowerShell como administrador o inicialo desde services.msc."
    }
} else {
    Write-Host "  $($pg.Name) ya estaba corriendo."
}

# --- 2. Ollama ---
Step 'Ollama'
if (Test-Url $OllamaUrl) {
    Write-Host '  Ya estaba corriendo.'
} else {
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw 'No se encontro ollama en el PATH.' }
    # Proceso suelto: sobrevive al cerrar esta ventana.
    Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden
    Wait-Url 'Ollama' $OllamaUrl 60
}

# --- 3. Qdrant (binario nativo, sin Docker) ---
Step 'Qdrant'
if (Test-Url $QdrantUrl) {
    Write-Host '  Ya estaba corriendo.'
} else {
    $exe = Join-Path $QdrantDir 'qdrant.exe'
    if (-not (Test-Path $exe)) { throw 'Falta qdrant.exe. Ejecuta antes .\scripts\setup-qdrant.ps1' }
    # Desde su carpeta: ahi estan su almacenamiento y el dashboard.
    Start-Process -FilePath $exe -WorkingDirectory $QdrantDir -WindowStyle Hidden
    Wait-Url 'Qdrant' $QdrantUrl 60
}

# --- 4. Precarga del modelo de chat ---
# Desde un HDD cargarlo tarda minutos; sin esto lo paga la primera pregunta.
Step 'Modelo de chat'
if (-not (Test-Path $Python)) { throw "Falta el entorno virtual del backend ($Python)." }
Push-Location $Backend
try {
    $model = & $Python -c "from app.core.config import settings; print(settings.LLM_MODEL)"
} finally {
    Pop-Location
}
$loaded = (Invoke-RestMethod 'http://127.0.0.1:11434/api/ps').models.name
if ($loaded -contains $model) {
    Write-Host "  $model ya estaba cargado."
} else {
    Write-Host "  Cargando $model (puede tardar unos minutos la primera vez)..."
    try {
        $body = @{ model = $model; prompt = ''; keep_alive = -1 } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/generate' -Body $body -ContentType 'application/json' -TimeoutSec 600 | Out-Null
        Write-Host "  $model cargado." -ForegroundColor Green
    } catch {
        # 404: el modelo no esta descargado en esta maquina.
        Write-Warning "No se pudo cargar $model ($($_.Exception.Message)). Revisa 'ollama list'."
    }
}

# --- 5. Backend ---
Step 'Backend'
if (Test-Url $BackendUrl) {
    Write-Host '  Ya estaba corriendo.'
} else {
    # Ventana propia para ver los logs; cerrarla detiene el backend.
    $cmd = "Set-Location '$Backend'; & '$Python' -m uvicorn app.main:app --reload --no-access-log"
    Start-Process -FilePath 'powershell' -ArgumentList '-NoExit', '-Command', $cmd
    # El arranque precarga el OCR y el reranker: la primera vez descarga sus modelos.
    Wait-Url 'Backend' $BackendUrl 300
}

# --- 6. Frontend ---
if (-not $NoFrontend) {
    Step 'Frontend'
    if (Test-Url $FrontUrl) {
        Write-Host '  Ya estaba corriendo.'
    } else {
        $cmd = "Set-Location '$Frontend'; npm start"
        Start-Process -FilePath 'powershell' -ArgumentList '-NoExit', '-Command', $cmd
        Wait-Url 'Frontend' $FrontUrl 300
    }
}

# --- Resumen ---
$health = Invoke-RestMethod $BackendUrl
Write-Host "`nSara lista." -ForegroundColor Green
Write-Host "  BD: $($health.database) | Qdrant: $($health.qdrant) | Ollama: $($health.ollama)"
Write-Host "  API:      http://127.0.0.1:8000/docs"
if (-not $NoFrontend) { Write-Host "  Frontend: $FrontUrl" }
