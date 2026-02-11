# TİB Takip Bot

Türkiye'deki internet sansürünü izlemek için Telegram botu.

## 🚀 Özellikler

- ✅ Multi-domain takibi (birden fazla domain izlenebilir)
- 🔄 Otomatik 5 dakikalık kontrol aralığı
- 🔍 Anlık domain kontrolü
- 📊 Durum değişikliği bildirimleri
- 🤖 CAPTCHA otomatik çözme (EasyOCR)
- 💾 Verileriniz kalıcı olarak saklanır
- 🔐 BTK'nın resmi sitesinden kontrol

## 📋 Kurulum

### Tek Komut Kurulum

```bash
sudo bash install_bot.sh
```

### Manuel Kurulum

1. Gerekli paketleri kurun:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

2. Sanal ortam oluşturun:
```bash
cd /home/claude
python3 -m venv venv
source venv/bin/activate
```

3. Python paketlerini kurun:
```bash
pip install python-telegram-bot aiohttp beautifulsoup4 easyocr pillow numpy opencv-python-headless torch torchvision
```

4. Botu çalıştırın:
```bash
python3 tib_takip_bot.py
```

## 🎮 Kullanım

1. Telegram'da @tibtakip_bot adresine gidin
2. `/start` komutunu gönderin
3. "➕ Domain Ekle" butonuna basın ve izlemek istediğiniz domain'i gönderin
4. "▶️ İzlemeyi Başlat" butonuna basarak otomatik izlemeyi başlatın
5. Durum değişikliklerinde bildirim alacaksınız!

## 📱 Telegram Komutları

- `/start` - Botu başlat ve ana menüyü göster
- `/help` - Yardım mesajını göster
- `/cancel` - Devam eden işlemi iptal et

## 🔧 Bot Yönetimi

### Servis Durumu
```bash
sudo systemctl status tib-takip-bot
```

### Logları Görüntüleme
```bash
sudo journalctl -u tib-takip-bot -f
```

### Yeniden Başlatma
```bash
sudo systemctl restart tib-takip-bot
```

### Durdurma
```bash
sudo systemctl stop tib-takip-bot
```

### Başlatma
```bash
sudo systemctl start tib-takip-bot
```

## 🛠️ Teknik Detaylar

- **Dil:** Python 3
- **Framework:** python-telegram-bot (async)
- **OCR:** EasyOCR (CPU mode)
- **Web Scraping:** aiohttp + BeautifulSoup
- **Veri:** JSON dosyası (/home/claude/tib_bot_data.json)

## 📊 Sistem Gereksinimleri

- Ubuntu 22.04 veya üzeri
- Python 3.8+
- En az 2 GB RAM
- En az 5 GB disk alanı
- İnternet bağlantısı

## 🔒 Güvenlik

- Bot tokeni güvenli şekilde saklanmalıdır
- Sadece güvendiğiniz kişilerle paylaşın
- VPS'nizde güvenlik duvarı ayarlarını yapın

## 📝 Notlar

- Bot, BTK'nın resmi sitesinden (internet.btk.gov.tr/sitesorgu/) kontrol yapar
- CAPTCHA çözme başarı oranı %80-95 arasındadır
- Her kontrol yaklaşık 5-10 saniye sürer
- Rate limiting nedeniyle 5 dakikalık aralık önerilir

## 🐛 Sorun Giderme

### Bot Başlamıyor
```bash
sudo journalctl -u tib-takip-bot -n 50
```

### CAPTCHA Çözülmüyor
- EasyOCR'ın düzgün kurulduğundan emin olun
- Yeterli RAM olup olmadığını kontrol edin

### Bildirim Gelmiyor
- İzlemenin başlatıldığından emin olun
- Domain'in doğru eklendiğini kontrol edin

## 📞 İletişim

- **Bot:** @tibtakip_bot
- **GitHub:** [Proje linki]

## 📜 Lisans

Bu proje açık kaynak kodludur. Özgürce kullanabilir ve geliştirebilirsiniz.

## ⚠️ Sorumluluk Reddi

Bu bot yalnızca bilgilendirme amaçlıdır. Kullanıcılar kendi sorumluluklarında kullanmalıdır.
