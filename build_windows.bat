@echo off
chcp 65001 > nul
echo ========================================================
echo   Teklif Sablonu - Windows .EXE Paketleme Betigi
echo ========================================================
echo.

REM 1. Python kontrolü
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.11 veya uzerini kurup PATH'e ekleyin.
    pause
    exit /b 1
)

REM 2. Sanal ortam olusturma/etkinlestirme
if not exist ".venv" (
    echo [*] Sanal ortam olusturuluyor (.venv)...
    python -m venv .venv
)

echo [*] Sanal ortam etkinlestiriliyor...
call .venv\Scripts\activate.bat

REM 3. Bagimliliklari yukleme
echo [*] Bagimliliklar kontrol ediliyor ve yukleniyor...
pip install --upgrade pip
pip install -e ".[dev]"
pip install pyinstaller

REM 4. PyInstaller ile derleme
echo [*] PyInstaller ile Windows .exe paketi derleniyor...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

pyinstaller --clean teklif_sablonu.spec

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Paketleme basarisiz oldu!
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo [BASARILI] Paketleme tamamlandi!
echo Cikti konumu: dist\TeklifSablonu.exe
echo ========================================================
echo.
pause
