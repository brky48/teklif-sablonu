# Windows PowerShell Derleme Betigi
# Teklif Sablonu - PyInstaller ile .exe Üretimi

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Teklif Sablonu - Windows .EXE Paketleme Betigi (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Python kontrolü
try {
    $pyVer = & python --version 2>&1
    Write-Host "[+] Python tespit edildi: $pyVer" -ForegroundColor Green
} catch {
    Write-Error "[-] Python bulunamadi! Lutfen Python 3.11 veya uzerini kurup PATH'e ekleyin."
    exit 1
}

# 2. Sanal ortam kontrolü
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Sanal ortam olusturuluyor (.venv)..." -ForegroundColor Yellow
    & python -m venv .venv
}

Write-Host "[*] Sanal ortam etkinlestiriliyor..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# 3. Bagimliliklari yukle
Write-Host "[*] Bagimliliklar yukleniyor..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& pip install -e ".[dev]"
& pip install pyinstaller

# 4. Derleme
Write-Host "[*] PyInstaller derlemesi baslatiliyor..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

& pyinstaller --clean teklif_sablonu.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "[BASARILI] Paketleme tamamlandi!" -ForegroundColor Green
    Write-Host "Calistirilabilir dosya: dist\TeklifSablonu.exe" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Host "[-] Derleme basarisiz oldu! Hata kodu: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
