#!/bin/bash
# TİB Takip Bot - Tek Komut Kurulum ve Çalıştırma

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================"
echo "TİB Takip Bot - Hızlı Başlangıç"
echo -e "======================================${NC}"
echo ""

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Bu scripti root olarak çalıştırmalısınız${NC}"
    echo "Kullanım: sudo bash quick_start.sh"
    exit 1
fi

# Dosya kontrolü
if [ ! -f "install_bot.sh" ]; then
    echo -e "${RED}❌ install_bot.sh dosyası bulunamadı!${NC}"
    exit 1
fi

if [ ! -f "tib_takip_bot.py" ]; then
    echo -e "${RED}❌ tib_takip_bot.py dosyası bulunamadı!${NC}"
    exit 1
fi

# İzin ver
chmod +x install_bot.sh
chmod +x tib_takip_bot.py

# Kurulumu başlat
echo -e "${YELLOW}🚀 Kurulum başlatılıyor...${NC}"
echo ""
bash install_bot.sh

# Sonuç
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================"
    echo "✅ HAZIR!"
    echo -e "======================================${NC}"
    echo ""
    echo "📱 Telegram'dan @tibtakip_bot adresine /start yazın"
    echo ""
else
    echo ""
    echo -e "${RED}======================================"
    echo "❌ HATA OLUŞTU"
    echo -e "======================================${NC}"
    echo ""
    echo "Logları kontrol edin:"
    echo "sudo journalctl -u tib-takip-bot -n 50"
    echo ""
fi
