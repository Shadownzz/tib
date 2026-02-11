# ============================================
# TİB TAKİP BOT - KURULUM REHBERİ
# ============================================

## 🚀 TEK KOMUT KURULUM

VPS sunucunuza SSH ile bağlanın ve aşağıdaki komutu çalıştırın:

```bash
cd /home/claude && sudo bash install_bot.sh
```

VEYA hızlı başlangıç için:

```bash
cd /home/claude && sudo bash quick_start.sh
```

## 📋 KURULUM ADIMLARI

1. VPS'nize bağlanın:
   ```bash
   ssh root@89.252.152.142
   ```

2. Kurulum scriptini çalıştırın:
   ```bash
   cd /home/claude
   sudo bash install_bot.sh
   ```

3. Kurulum tamamlandıktan sonra:
   - Telegram'dan @tibtakip_bot adresine gidin
   - /start komutunu gönderin
   - Bot kullanıma hazır!

## 🔧 BOT YÖNETİMİ

### Durum Kontrolü
```bash
sudo systemctl status tib-takip-bot
```

### Logları Görüntüleme (Canlı)
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

## 📱 TELEGRAM KULLANIMI

1. Bot'u başlatın: /start
2. Domain ekleyin: "➕ Domain Ekle" → domain adresini gönderin
3. İzlemeyi başlatın: "▶️ İzlemeyi Başlat"
4. İşte bu kadar! Durum değişikliklerinde bildirim alacaksınız.

## 🎯 ÖZELLİKLER

✅ Multi-domain takibi (sınırsız domain)
✅ Otomatik CAPTCHA çözme
✅ 5 dakikalık kontrol aralığı
✅ Anlık sorgulama
✅ Durum değişikliği bildirimleri
✅ Kalıcı veri saklama
✅ Kullanıcı dostu arayüz

## 🐛 SORUN GİDERME

### Bot çalışmıyor:
```bash
sudo journalctl -u tib-takip-bot -n 100
```

### Manuel başlatma (test için):
```bash
cd /home/claude
source venv/bin/activate
python3 tib_takip_bot.py
```

### Servisi yeniden yükle:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tib-takip-bot
```

## 📊 SİSTEM GEREKSİNİMLERİ

✅ Ubuntu 22.04 (mevcut)
✅ 2 GB RAM (mevcut: 1.91 GB)
✅ 5 GB disk (mevcut: 39.44 GB)
✅ Python 3.8+
✅ İnternet bağlantısı

## 🔒 GÜVENLİK

⚠️ Bot token'ı güvenli tutun
⚠️ Sadece güvendiğiniz kişilerle paylaşın
⚠️ Firewall ayarlarını yapın (opsiyonel)

## 📞 İLETİŞİM

🤖 Bot: @tibtakip_bot
💻 VPS: 89.252.152.142

## ⚡ HIZLI BAŞLANGIÇ KOMUTLARI

Tüm kurulum tek komutla:
```bash
cd /home/claude && sudo bash install_bot.sh
```

Logları izle:
```bash
sudo journalctl -u tib-takip-bot -f
```

Yeniden başlat:
```bash
sudo systemctl restart tib-takip-bot
```

## 🎉 KURULUM TAMAMLANDI!

Bot artık çalışıyor ve kullanıma hazır!
Telegram'dan @tibtakip_bot adresine /start yazarak başlayın.
