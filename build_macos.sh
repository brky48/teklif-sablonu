#!/usr/bin/env bash
# macOS Derleme Betiği
# Teklif Şablonu - PyInstaller ile .app Paketi Üretimi

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================================${NC}"
echo -e "${CYAN}  Teklif Şablonu - macOS .APP Paketleme Betiği           ${NC}"
echo -e "${CYAN}========================================================${NC}"
echo ""

# 1. Proje kök dizinine geç
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Python kontrolü
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[HATA] python3 bulunamadı! Lütfen Python 3.11 veya üzerini kurun.${NC}"
    exit 1
fi

PY_VER=$(python3 --version 2>&1)
echo -e "${GREEN}[+] Python tespit edildi: ${PY_VER}${NC}"

# 3. Sanal ortam kontrolü
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}[*] Sanal ortam oluşturuluyor (.venv)...${NC}"
    python3 -m venv .venv
fi

echo -e "${YELLOW}[*] Sanal ortam etkinleştiriliyor...${NC}"
source .venv/bin/activate

# 4. Bağımlılıkları kontrol et / yükle
echo -e "${YELLOW}[*] Bağımlılıklar güncelleniyor...${NC}"
pip install --upgrade pip
pip install -e ".[dev]"

# 5. Temizlik ve Derleme
echo -e "${YELLOW}[*] Önceki derleme artıkları temizleniyor...${NC}"
rm -rf build dist

echo -e "${YELLOW}[*] PyInstaller ile macOS .app paketi derleniyor...${NC}"
pyinstaller --clean teklif_sablonu.spec

# 6. macOS Karantina / İzin ayarları
if [ -d "dist/TeklifSablonu.app" ]; then
    echo -e "${YELLOW}[*] macOS güvenlik/karantina öznitelikleri temizleniyor...${NC}"
    xattr -cr "dist/TeklifSablonu.app" || true

    echo ""
    echo -e "${GREEN}========================================================${NC}"
    echo -e "${GREEN}[BAŞARILI] macOS paketleme tamamlandı!                   ${NC}"
    echo -e "${GREEN}Çıktı konumu: dist/TeklifSablonu.app                     ${NC}"
    echo -e "${GREEN}========================================================${NC}"
    echo ""
    echo -e "Çalıştırmak için:"
    echo -e "  open dist/TeklifSablonu.app"
    echo -e "veya dist/TeklifSablonu.app uygulamasını 'Uygulamalar' (Applications) klasörüne sürükleyebilirsiniz."
    echo ""
else
    echo -e "${RED}[HATA] dist/TeklifSablonu.app oluşturulamadı!${NC}"
    exit 1
fi
