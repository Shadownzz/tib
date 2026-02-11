#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Set, List
import aiohttp
from bs4 import BeautifulSoup
import easyocr
import numpy as np
from PIL import Image
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8558544272:AAFm2TTVplNrxOLCuoMg03EaG1EX9Qlth0o"

# Global değişkenler
monitored_domains: Dict[int, Set[str]] = {}  # chat_id -> domain listesi
domain_status: Dict[str, Dict] = {}  # domain -> status bilgisi
monitoring_tasks: Dict[int, asyncio.Task] = {}  # chat_id -> monitoring task

# EasyOCR reader (global olarak bir kez yüklenir)
reader = None

# Data dosyası
DATA_FILE = "/home/claude/tib_bot_data.json"

def load_data():
    """Kayıtlı verileri yükle"""
    global monitored_domains, domain_status
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # String anahtarları integer'a çevir
                monitored_domains = {int(k): set(v) for k, v in data.get('monitored_domains', {}).items()}
                domain_status = data.get('domain_status', {})
                logger.info("Veriler yüklendi")
    except Exception as e:
        logger.error(f"Veri yükleme hatası: {e}")

def save_data():
    """Verileri kaydet"""
    try:
        data = {
            'monitored_domains': {str(k): list(v) for k, v in monitored_domains.items()},
            'domain_status': domain_status
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Veriler kaydedildi")
    except Exception as e:
        logger.error(f"Veri kaydetme hatası: {e}")

async def init_ocr():
    """EasyOCR'ı başlat"""
    global reader
    if reader is None:
        logger.info("EasyOCR yükleniyor...")
        reader = easyocr.Reader(['tr', 'en'], gpu=False)
        logger.info("EasyOCR yüklendi")

def clean_domain(domain: str) -> str:
    """Domain adresini temizle"""
    domain = domain.strip().lower()
    # http://, https://, www. kısımlarını kaldır
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    # Son / işaretini kaldır
    domain = domain.rstrip('/')
    return domain

async def solve_captcha(image_bytes: bytes) -> str:
    """CAPTCHA'yı EasyOCR ile çöz"""
    try:
        # Resmi numpy array'e çevir
        image = Image.open(BytesIO(image_bytes))
        image_np = np.array(image)
        
        # OCR işlemi
        result = reader.readtext(image_np, detail=0)
        
        if result:
            # Tüm sonuçları birleştir ve temizle
            captcha_text = ''.join(result)
            # Sadece alfanumerik karakterleri al
            captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
            logger.info(f"CAPTCHA çözüldü: {captcha_text}")
            return captcha_text
        else:
            logger.warning("CAPTCHA çözülemedi")
            return ""
    except Exception as e:
        logger.error(f"CAPTCHA çözme hatası: {e}")
        return ""

async def check_domain_status(domain: str) -> tuple[bool, str]:
    """
    Domain'in TİB tarafından engellenip engellenmediğini kontrol et
    Returns: (engellendi_mi, mesaj)
    """
    url = "https://internet.btk.gov.tr/sitesorgu/"
    
    try:
        async with aiohttp.ClientSession() as session:
            # İlk sayfa yüklemesi
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # CAPTCHA resmini al
                captcha_img = soup.find('img', {'id': 'security_code_image'})
                if not captcha_img or 'src' not in captcha_img.attrs:
                    return False, "⚠️ CAPTCHA resmi bulunamadı"
                
                captcha_url = captcha_img['src']
                if not captcha_url.startswith('http'):
                    captcha_url = url + captcha_url.lstrip('/')
                
                # CAPTCHA resmini indir
                async with session.get(captcha_url, timeout=aiohttp.ClientTimeout(total=30)) as img_response:
                    captcha_bytes = await img_response.read()
                
                # CAPTCHA'yı çöz
                captcha_text = await solve_captcha(captcha_bytes)
                
                if not captcha_text:
                    return False, "⚠️ CAPTCHA çözülemedi"
                
                # Form verilerini hazırla
                form_data = {
                    'url': domain,
                    'security_code': captcha_text,
                    'submit': 'Sorgula'
                }
                
                # Formu gönder
                async with session.post(url, data=form_data, timeout=aiohttp.ClientTimeout(total=30)) as post_response:
                    result_html = await post_response.text()
                    result_soup = BeautifulSoup(result_html, 'html.parser')
                    
                    # Sonuç metnini bul
                    result_span = result_soup.find('span', {'class': 'yazi2_2'})
                    
                    if result_span:
                        result_text = result_span.get_text(strip=True)
                        
                        # Engellenmemiş kontrolü
                        if "Bilgi Teknolojileri ve İletişim Kurumu tarafından uygulanan bir karar bulunamadı" in result_text:
                            return False, "✅ Domain engellenmiş değil"
                        else:
                            # Engellenmiş
                            return True, f"🚫 Domain yasaklanmıştır!\n\n{result_text}"
                    else:
                        return False, "⚠️ Sonuç metni bulunamadı (CAPTCHA yanlış olabilir)"
                        
    except asyncio.TimeoutError:
        return False, "⏱️ Zaman aşımı - Site yanıt vermiyor"
    except Exception as e:
        logger.error(f"Domain kontrol hatası: {e}")
        return False, f"⚠️ Hata: {str(e)}"

async def monitor_domains(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Belirli bir chat için domain'leri sürekli izle"""
    logger.info(f"Chat {chat_id} için izleme başlatıldı")
    
    while chat_id in monitored_domains and monitored_domains[chat_id]:
        try:
            for domain in list(monitored_domains[chat_id]):
                is_blocked, message = await check_domain_status(domain)
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Önceki durum
                previous_status = domain_status.get(domain, {}).get('blocked', None)
                
                # Durum değişikliği kontrolü
                if previous_status is not None and previous_status != is_blocked:
                    # Durum değişti!
                    if is_blocked:
                        # Yeni engelleme
                        alert_message = f"🚨 YENİ ENGELLEME TESPİT EDİLDİ! 🚨\n\n"
                        alert_message += f"🌐 Domain: {domain}\n"
                        alert_message += f"📅 Tarih: {current_time}\n\n"
                        alert_message += message
                    else:
                        # Engel kaldırıldı
                        alert_message = f"✅ ENGEL KALDIRILDI! ✅\n\n"
                        alert_message += f"🌐 Domain: {domain}\n"
                        alert_message += f"📅 Tarih: {current_time}\n\n"
                        alert_message += message
                    
                    await context.bot.send_message(chat_id=chat_id, text=alert_message)
                
                # İlk kontrolde bildirim yap
                elif previous_status is None:
                    initial_message = f"ℹ️ İLK KONTROL SONUCU\n\n"
                    initial_message += f"🌐 Domain: {domain}\n"
                    initial_message += f"📅 Tarih: {current_time}\n\n"
                    initial_message += message
                    await context.bot.send_message(chat_id=chat_id, text=initial_message)
                
                # Durumu kaydet
                domain_status[domain] = {
                    'blocked': is_blocked,
                    'last_check': current_time,
                    'message': message
                }
                
                save_data()
                
                # Rate limiting için bekle
                await asyncio.sleep(2)
            
            # 5 dakika bekle
            await asyncio.sleep(300)
            
        except asyncio.CancelledError:
            logger.info(f"Chat {chat_id} için izleme durduruldu")
            break
        except Exception as e:
            logger.error(f"İzleme döngüsü hatası: {e}")
            await asyncio.sleep(60)  # Hata durumunda 1 dakika bekle

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komutu"""
    keyboard = [
        [InlineKeyboardButton("➕ Domain Ekle", callback_data='add_domain')],
        [InlineKeyboardButton("🗑️ Domain Sil", callback_data='remove_domain')],
        [InlineKeyboardButton("📋 Domain Listesi", callback_data='list_domains')],
        [InlineKeyboardButton("🔍 Anlık Kontrol", callback_data='instant_check')],
        [InlineKeyboardButton("▶️ İzlemeyi Başlat", callback_data='start_monitoring')],
        [InlineKeyboardButton("⏸️ İzlemeyi Durdur", callback_data='stop_monitoring')],
        [InlineKeyboardButton("❓ Yardım", callback_data='help')],
        [InlineKeyboardButton("📞 İletişim", callback_data='contact')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🤖 TİB Takip Botu'na Hoş Geldiniz!

Bu bot, Türkiye'deki internet sansürünü izlemenize yardımcı olur.

🔹 Domain ekleyip izlemeye alabilirsiniz
🔹 5 dakikada bir otomatik kontrol yapılır
🔹 Durum değişikliklerinde bildirim alırsınız
🔹 Anlık kontrol yapabilirsiniz

Başlamak için aşağıdaki butonları kullanın:
"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım mesajı"""
    query = update.callback_query
    if query:
        await query.answer()
    
    help_text = """
📖 TİB Takip Botu Kullanım Kılavuzu

🔹 DOMAIN EKLEME:
"➕ Domain Ekle" butonuna basın ve domain adresini gönderin.
Örnek: example.com veya www.example.com

🔹 DOMAIN SİLME:
"🗑️ Domain Sil" butonuna basın ve silmek istediğiniz domain'i seçin.

🔹 LİSTELEME:
"📋 Domain Listesi" ile izlenen tüm domain'leri ve durumlarını görüntüleyin.

🔹 ANLIK KONTROL:
"🔍 Anlık Kontrol" ile seçtiğiniz domain'i hemen kontrol edin.

🔹 İZLEME BAŞLATMA:
"▶️ İzlemeyi Başlat" ile otomatik izlemeyi başlatın (5 dk aralıklarla).

🔹 İZLEME DURDURMA:
"⏸️ İzlemeyi Durdur" ile otomatik izlemeyi durdurun.

⚠️ NOT: Bot, BTK'nın resmi sitesinden (internet.btk.gov.tr) kontrol yapar.
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(help_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup)

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """İletişim bilgileri"""
    query = update.callback_query
    await query.answer()
    
    contact_text = """
📞 İletişim Bilgileri

🤖 Bot: @tibtakip_bot
💻 GitHub: [Proje bağlantınız]
✉️ E-posta: [E-posta adresiniz]

🐛 Hata bildirimi veya önerileriniz için iletişime geçebilirsiniz.

⭐ Projeyi beğendiyseniz GitHub'da yıldız vermeyi unutmayın!
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(contact_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklamalarını yönet"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    if query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("➕ Domain Ekle", callback_data='add_domain')],
            [InlineKeyboardButton("🗑️ Domain Sil", callback_data='remove_domain')],
            [InlineKeyboardButton("📋 Domain Listesi", callback_data='list_domains')],
            [InlineKeyboardButton("🔍 Anlık Kontrol", callback_data='instant_check')],
            [InlineKeyboardButton("▶️ İzlemeyi Başlat", callback_data='start_monitoring')],
            [InlineKeyboardButton("⏸️ İzlemeyi Durdur", callback_data='stop_monitoring')],
            [InlineKeyboardButton("❓ Yardım", callback_data='help')],
            [InlineKeyboardButton("📞 İletişim", callback_data='contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Ana Menü:", reply_markup=reply_markup)
    
    elif query.data == 'add_domain':
        await query.edit_message_text(
            "➕ Eklemek istediğiniz domain adresini gönderin:\n\n"
            "Örnek: example.com veya www.example.com\n\n"
            "İptal için /cancel yazın."
        )
        context.user_data['waiting_for'] = 'domain_add'
    
    elif query.data == 'remove_domain':
        if chat_id not in monitored_domains or not monitored_domains[chat_id]:
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ İzlenen domain bulunmuyor.",
                reply_markup=reply_markup
            )
        else:
            keyboard = []
            for domain in sorted(monitored_domains[chat_id]):
                keyboard.append([InlineKeyboardButton(
                    f"🗑️ {domain}",
                    callback_data=f'remove_{domain}'
                )])
            keyboard.append([InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Silmek istediğiniz domain'i seçin:",
                reply_markup=reply_markup
            )
    
    elif query.data.startswith('remove_'):
        domain = query.data[7:]  # 'remove_' kısmını çıkar
        if chat_id in monitored_domains and domain in monitored_domains[chat_id]:
            monitored_domains[chat_id].remove(domain)
            if not monitored_domains[chat_id]:
                del monitored_domains[chat_id]
            save_data()
            
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ {domain} silindi.",
                reply_markup=reply_markup
            )
    
    elif query.data == 'list_domains':
        if chat_id not in monitored_domains or not monitored_domains[chat_id]:
            text = "❌ İzlenen domain bulunmuyor."
        else:
            text = "📋 İzlenen Domain'ler:\n\n"
            for domain in sorted(monitored_domains[chat_id]):
                status_info = domain_status.get(domain, {})
                blocked = status_info.get('blocked', None)
                last_check = status_info.get('last_check', 'Henüz kontrol edilmedi')
                
                if blocked is None:
                    status_emoji = "⏳"
                    status_text = "Kontrol bekleniyor"
                elif blocked:
                    status_emoji = "🚫"
                    status_text = "ENGELLİ"
                else:
                    status_emoji = "✅"
                    status_text = "Erişilebilir"
                
                text += f"{status_emoji} {domain}\n"
                text += f"   Durum: {status_text}\n"
                text += f"   Son kontrol: {last_check}\n\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == 'instant_check':
        if chat_id not in monitored_domains or not monitored_domains[chat_id]:
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ İzlenen domain bulunmuyor. Önce domain ekleyin.",
                reply_markup=reply_markup
            )
        else:
            keyboard = []
            for domain in sorted(monitored_domains[chat_id]):
                keyboard.append([InlineKeyboardButton(
                    f"🔍 {domain}",
                    callback_data=f'check_{domain}'
                )])
            keyboard.append([InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Kontrol etmek istediğiniz domain'i seçin:",
                reply_markup=reply_markup
            )
    
    elif query.data.startswith('check_'):
        domain = query.data[6:]  # 'check_' kısmını çıkar
        await query.edit_message_text(f"🔍 {domain} kontrol ediliyor...\n\nLütfen bekleyin...")
        
        is_blocked, message = await check_domain_status(domain)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result_text = f"📊 KONTROL SONUCU\n\n"
        result_text += f"🌐 Domain: {domain}\n"
        result_text += f"📅 Tarih: {current_time}\n\n"
        result_text += message
        
        # Durumu kaydet
        domain_status[domain] = {
            'blocked': is_blocked,
            'last_check': current_time,
            'message': message
        }
        save_data()
        
        keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(result_text, reply_markup=reply_markup)
    
    elif query.data == 'start_monitoring':
        if chat_id not in monitored_domains or not monitored_domains[chat_id]:
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ İzlenen domain bulunmuyor. Önce domain ekleyin.",
                reply_markup=reply_markup
            )
        elif chat_id in monitoring_tasks:
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "ℹ️ İzleme zaten aktif.",
                reply_markup=reply_markup
            )
        else:
            # İzleme görevini başlat
            task = asyncio.create_task(monitor_domains(chat_id, context))
            monitoring_tasks[chat_id] = task
            
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            domain_count = len(monitored_domains[chat_id])
            await query.edit_message_text(
                f"▶️ İzleme başlatıldı!\n\n"
                f"📊 {domain_count} domain izleniyor\n"
                f"⏱️ Kontrol aralığı: 5 dakika\n\n"
                f"Durum değişikliklerinde bildirim alacaksınız.",
                reply_markup=reply_markup
            )
    
    elif query.data == 'stop_monitoring':
        if chat_id in monitoring_tasks:
            monitoring_tasks[chat_id].cancel()
            del monitoring_tasks[chat_id]
            
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "⏸️ İzleme durduruldu.",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("◀️ Ana Menü", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "ℹ️ Aktif izleme bulunmuyor.",
                reply_markup=reply_markup
            )
    
    elif query.data == 'help':
        await help_command(update, context)
    
    elif query.data == 'contact':
        await contact_command(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mesaj yöneticisi"""
    chat_id = update.message.chat_id
    text = update.message.text
    
    if text == '/cancel':
        context.user_data.clear()
        await update.message.reply_text("❌ İşlem iptal edildi.")
        return
    
    if context.user_data.get('waiting_for') == 'domain_add':
        domain = clean_domain(text)
        
        if not domain:
            await update.message.reply_text("❌ Geçersiz domain. Tekrar deneyin veya /cancel ile iptal edin.")
            return
        
        if chat_id not in monitored_domains:
            monitored_domains[chat_id] = set()
        
        if domain in monitored_domains[chat_id]:
            await update.message.reply_text(f"ℹ️ {domain} zaten izleniyor.")
        else:
            monitored_domains[chat_id].add(domain)
            save_data()
            await update.message.reply_text(
                f"✅ {domain} eklendi!\n\n"
                f"İzlemeyi başlatmak için /start komutunu kullanın ve "
                f"'▶️ İzlemeyi Başlat' butonuna basın."
            )
        
        context.user_data.clear()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hata yöneticisi"""
    logger.error(f"Update {update} caused error {context.error}")

async def post_init(application: Application):
    """Bot başlatıldığında çalışır"""
    await init_ocr()
    load_data()
    logger.info("Bot hazır!")

def main():
    """Ana fonksiyon"""
    # Application oluştur
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Handler'ları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)
    
    # Botu başlat
    logger.info("Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
