#!/bin/bash

# TİB Takip Bot Kurulum Scripti
# Bu script tüm gereksinimleri kurar ve botu başlatır

set -e  # Hata durumunda dur

echo "======================================"
echo "TİB Takip Bot Kurulum Başlatılıyor"
echo "======================================"
echo ""

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Bu scripti root olarak çalıştırmalısınız (sudo kullanın)"
    exit 1
fi

# Sistem güncellemesi
echo "📦 Sistem güncelleniyor..."
apt update -qq
apt upgrade -y -qq

# Gerekli sistem paketlerini kur
echo "📦 Sistem paketleri kuruluyor..."
apt install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgeos-dev \
    git \
    wget \
    curl

# Python sanal ortamı oluştur
echo "🐍 Python sanal ortamı oluşturuluyor..."
cd /home/claude
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate

# Pip'i güncelle
echo "📦 Pip güncelleniyor..."
pip install --upgrade pip setuptools wheel -q

# Python paketlerini kur
echo "📦 Python paketleri kuruluyor (bu biraz zaman alabilir)..."
pip install -q \
    python-telegram-bot==20.8 \
    aiohttp==3.9.1 \
    beautifulsoup4==4.12.2 \
    easyocr==1.7.1 \
    pillow==10.1.0 \
    numpy==1.24.3 \
    opencv-python-headless==4.8.1.78 \
    torch==2.1.2 \
    torchvision==0.16.2

# Bot script'ini oluştur (eğer yoksa)
if [ ! -f "/home/claude/tib_takip_bot.py" ]; then
    echo "❌ tib_takip_bot.py dosyası bulunamadı!"
    echo "Lütfen önce bot scriptini /home/claude/tib_takip_bot.py konumuna kaydedin."
    exit 1
fi

# Script'e çalıştırma izni ver
chmod +x /home/claude/tib_takip_bot.py

# Systemd servis dosyası oluştur
echo "⚙️ Systemd servisi oluşturuluyor..."
cat > /etc/systemd/system/tib-takip-bot.service << 'EOF'
[Unit]
Description=TIB Takip Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/claude
Environment="PATH=/home/claude/venv/bin"
ExecStart=/home/claude/venv/bin/python3 /home/claude/tib_takip_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Servisi etkinleştir ve başlat
echo "🚀 Servis başlatılıyor..."
systemctl daemon-reload
systemctl enable tib-takip-bot.service
systemctl restart tib-takip-bot.service

# Durum kontrolü
sleep 3
if systemctl is-active --quiet tib-takip-bot.service; then
    echo ""
    echo "======================================"
    echo "✅ KURULUM BAŞARIYLA TAMAMLANDI!"
    echo "======================================"
    echo ""
    echo "🤖 Bot bilgileri:"
    echo "   Telegram: @tibtakip_bot"
    echo ""
    echo "📋 Kullanışlı komutlar:"
    echo "   Durum kontrol: sudo systemctl status tib-takip-bot"
    echo "   Logları görüntüle: sudo journalctl -u tib-takip-bot -f"
    echo "   Yeniden başlat: sudo systemctl restart tib-takip-bot"
    echo "   Durdur: sudo systemctl stop tib-takip-bot"
    echo "   Başlat: sudo systemctl start tib-takip-bot"
    echo ""
    echo "🎉 Bot şu anda çalışıyor ve kullanıma hazır!"
    echo "   Telegram'dan @tibtakip_bot adresine /start yazarak başlayın."
    echo ""
else
    echo ""
    echo "======================================"
    echo "⚠️ UYARI: Servis başlatılamadı!"
    echo "======================================"
    echo ""
    echo "Hata detaylarını görmek için çalıştırın:"
    echo "sudo journalctl -u tib-takip-bot -n 50"
    echo ""
fi
