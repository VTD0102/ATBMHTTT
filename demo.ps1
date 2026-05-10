[CmdletBinding()]
param(
    [switch]$AttackOnly,
    [switch]$DefendOnly,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ShopData = Join-Path $ScriptDir "shop_data"
$Attacker = Join-Path $ScriptDir "manager-agent"
$Defender = Join-Path $ScriptDir "defender"
$Backups = Join-Path $ScriptDir "backups"
$Python310 = Join-Path $ScriptDir ".venv310\Scripts\python.exe"
$PythonVenv = Join-Path $ScriptDir "venv\Scripts\python.exe"

if ($Help) {
    Write-Host "Usage: .\demo.ps1 [-AttackOnly | -DefendOnly]"
    Write-Host "  no args      Full demo: attack + defense + recovery"
    Write-Host "  -AttackOnly  Chi chay phan tan cong"
    Write-Host "  -DefendOnly  Chi chay phan phong thu + phuc hoi"
    Write-Host "  -Help        Xem huong dan"
    exit 0
}

if ($AttackOnly -and $DefendOnly) {
    throw "Chi duoc chon mot trong hai tham so: -AttackOnly hoac -DefendOnly."
}

if (Test-Path -LiteralPath $Python310) {
    $Python = $Python310
} elseif (Test-Path -LiteralPath $PythonVenv) {
    $Python = $PythonVenv
} else {
    $Python = "python"
}

$Mode = "full"
if ($AttackOnly) { $Mode = "attack" }
if ($DefendOnly) { $Mode = "defend" }

function Write-Sep {
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor DarkCyan
}

function Write-Step([string]$Number, [string]$Message) {
    Write-Host ""
    Write-Host "[BUOC $Number] $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

function Write-Info([string]$Message) {
    Write-Host "  -> $Message" -ForegroundColor Blue
}

function Invoke-Python([string[]]$Arguments, [switch]$AllowFailure) {
    & $Python @Arguments
    $ExitCode = $LASTEXITCODE
    if (($ExitCode -ne 0) -and -not $AllowFailure) {
        throw "Python command failed with exit code ${ExitCode}: $Python $($Arguments -join ' ')"
    }
    return $ExitCode
}

function New-ShopBackup {
    if (-not (Test-Path -LiteralPath $Backups)) {
        New-Item -ItemType Directory -Path $Backups | Out-Null
    }
    Invoke-Python @((Join-Path $Defender "backup_manager.py"), "backup") | Out-Null
}

function Restore-LatestBackup {
    if (-not (Test-Path -LiteralPath $Backups)) {
        Write-Warn "Khong tim thay thu muc backups."
        return
    }

    $Latest = Get-ChildItem -LiteralPath $Backups -Filter "backup_*.tar.gz" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $Latest) {
        Write-Warn "Khong tim thay backup."
        return
    }

    if (Test-Path -LiteralPath $ShopData) {
        Get-ChildItem -LiteralPath $ShopData -Force | ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force
        }
    } else {
        New-Item -ItemType Directory -Path $ShopData | Out-Null
    }

    Invoke-Python @((Join-Path $Defender "backup_manager.py"), "restore", $Latest.FullName) | Out-Null
}

Write-Host ""
Write-Host "DEMO AN TOAN THONG TIN - ATBMHTTT" -ForegroundColor White
Write-Host "Mode: $Mode" -ForegroundColor Yellow
Write-Host "Python: $Python" -ForegroundColor DarkGray

if (($Mode -eq "full") -or ($Mode -eq "attack")) {
    Write-Sep
    Write-Step "1" "Backup du lieu shop truoc khi tan cong"
    New-ShopBackup
    Write-Ok "Da backup shop_data/"

    Write-Sep
    Write-Step "2" "Hien thi du lieu TMDT ban dau"
    Get-ChildItem -LiteralPath $ShopData -Force

    Write-Sep
    Write-Step "3" "KICH BAN TAN CONG: Nan nhan mo ProManager Suite"
    Write-Warn "Nan nhan duoc lua nhap API key vao phan mem gia mao"
    Write-Info "Chay: $Python manager-agent\fake_manager.py"
    Invoke-Python @((Join-Path $Attacker "fake_manager.py")) | Out-Null

    Write-Sep
    Write-Step "4" "Ket qua sau tan cong"
    Get-ChildItem -LiteralPath $ShopData -Force
    $EncryptedCount = @(Get-ChildItem -LiteralPath $ShopData -Filter "*.encrypted" -File -ErrorAction SilentlyContinue).Count
    if ($EncryptedCount -gt 0) {
        Write-Warn "$EncryptedCount file(s) da bi ma hoa."
    }
}

if (($Mode -eq "full") -or ($Mode -eq "defend")) {
    Write-Sep
    Write-Step "5" "Phan tich tinh (Static Analysis)"
    Write-Info "Quet file tan cong: manager-agent\fake_manager.py"
    $env:PYTHONIOENCODING = "utf-8"
    Invoke-Python @((Join-Path $Defender "static_analyzer.py"), (Join-Path $Attacker "fake_manager.py")) -AllowFailure | Out-Null

    Write-Sep
    Write-Step "6" "Quet phat hien ransomware trong shop_data/"
    Invoke-Python @((Join-Path $Defender "scanner.py"), $ShopData) -AllowFailure | Out-Null

    Write-Sep
    Write-Step "7" "Phuc hoi du lieu (Decryptor)"
    $KeyFile = Join-Path $ShopData ".ransom_key"
    if (Test-Path -LiteralPath $KeyFile) {
        Invoke-Python @((Join-Path $Defender "decryptor.py"), $ShopData) | Out-Null
    } else {
        Write-Warn "Khong tim thay .ransom_key. Phuc hoi tu backup..."
        Restore-LatestBackup
    }

    Write-Sep
    Write-Step "8" "Backup dinh ky sau khi phuc hoi"
    Invoke-Python @((Join-Path $Defender "backup_manager.py"), "backup") | Out-Null
    Invoke-Python @((Join-Path $Defender "backup_manager.py"), "list") | Out-Null

    Write-Sep
    Write-Step "9" "Ket qua sau phuc hoi"
    Get-ChildItem -LiteralPath $ShopData -Force
    Write-Ok "Du lieu da duoc phuc hoi."
}

Write-Sep
Write-Host ""
Write-Host "DEMO HOAN TAT" -ForegroundColor Green
Write-Host "MOI TRUONG HOC THUAT - DEMO ONLY" -ForegroundColor Yellow
