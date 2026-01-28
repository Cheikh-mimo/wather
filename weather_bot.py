"""
بوت تيليجرام للأرصاد الجوية في الجزائر
يعمل بالأزرار ويطلب من المستخدم اختيار الولاية والدائرة
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت (احصل عليه من @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# API Key للطقس (احصل عليه من openweathermap.org)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'YOUR_API_KEY_HERE')

# ولايات الجزائر (48 ولاية)
WILAYAS = {
    '01': 'أدرار',
    '02': 'الشلف',
    '03': 'الأغواط',
    '04': 'أم البواقي',
    '05': 'باتنة',
    '06': 'بجاية',
    '07': 'بسكرة',
    '08': 'بشار',
    '09': 'البليدة',
    '10': 'البويرة',
    '11': 'تمنراست',
    '12': 'تبسة',
    '13': 'تلمسان',
    '14': 'تيارت',
    '15': 'تيزي وزو',
    '16': 'الجزائر',
    '17': 'الجلفة',
    '18': 'جيجل',
    '19': 'سطيف',
    '20': 'سعيدة',
    '21': 'سكيكدة',
    '22': 'سيدي بلعباس',
    '23': 'عنابة',
    '24': 'قالمة',
    '25': 'قسنطينة',
    '26': 'المدية',
    '27': 'مستغانم',
    '28': 'المسيلة',
    '29': 'معسكر',
    '30': 'ورقلة',
    '31': 'وهران',
    '32': 'البيض',
    '33': 'إليزي',
    '34': 'برج بوعريريج',
    '35': 'بومرداس',
    '36': 'الطارف',
    '37': 'تندوف',
    '38': 'تيسمسيلت',
    '39': 'الوادي',
    '40': 'خنشلة',
    '41': 'سوق أهراس',
    '42': 'تيبازة',
    '43': 'ميلة',
    '44': 'عين الدفلى',
    '45': 'النعامة',
    '46': 'عين تموشنت',
    '47': 'غرداية',
    '48': 'غليزان'
}

# دوائر مختارة لكل ولاية (مثال - يمكنك إضافة المزيد)
DAIRAS = {
    '16': ['الجزائر الوسطى', 'باب الوادي', 'حسين داي', 'برج الكيفان', 'الدار البيضاء'],
    '31': ['وهران', 'السانية', 'بئر الجير', 'عين الترك', 'مرسى الحجاج'],
    '19': ['سطيف', 'العلمة', 'عين الكبيرة', 'بوقاعة', 'عين ولمان'],
    # يمكنك إضافة المزيد حسب الحاجة
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية مع أزرار اختيار الولاية"""
    
    # إنشاء أزرار الولايات (4 أزرار في كل صف)
    keyboard = []
    wilaya_items = list(WILAYAS.items())
    
    for i in range(0, len(wilaya_items), 4):
        row = []
        for code, name in wilaya_items[i:i+4]:
            row.append(InlineKeyboardButton(
                f"{name} ({code})",
                callback_data=f"wilaya_{code}"
            ))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🌤️ **مرحباً بك في بوت الأرصاد الجوية الجزائري!** 🇩🇿

أنا هنا لتقديم معلومات الطقس الحالية في جميع ولايات الجزائر.

📍 **اختر ولايتك من القائمة أدناه:**
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('wilaya_'):
        # اختيار الولاية
        wilaya_code = data.split('_')[1]
        wilaya_name = WILAYAS[wilaya_code]
        
        # التحقق من وجود دوائر لهذه الولاية
        if wilaya_code in DAIRAS:
            # عرض أزرار الدوائر
            keyboard = []
            for daira in DAIRAS[wilaya_code]:
                keyboard.append([InlineKeyboardButton(
                    daira,
                    callback_data=f"daira_{wilaya_code}_{daira}"
                )])
            
            # زر العودة
            keyboard.append([InlineKeyboardButton("🔙 العودة للولايات", callback_data="back_to_wilayas")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📍 **{wilaya_name}**\n\nاختر الدائرة:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # إذا لم تكن هناك دوائر، احصل على الطقس مباشرة للولاية
            await get_weather(query, wilaya_name, wilaya_name)
    
    elif data.startswith('daira_'):
        # اختيار الدائرة
        parts = data.split('_', 2)
        wilaya_code = parts[1]
        daira_name = parts[2]
        wilaya_name = WILAYAS[wilaya_code]
        
        # الحصول على معلومات الطقس
        await get_weather(query, wilaya_name, daira_name)
    
    elif data == 'back_to_wilayas':
        # العودة لقائمة الولايات
        keyboard = []
        wilaya_items = list(WILAYAS.items())
        
        for i in range(0, len(wilaya_items), 4):
            row = []
            for code, name in wilaya_items[i:i+4]:
                row.append(InlineKeyboardButton(
                    f"{name} ({code})",
                    callback_data=f"wilaya_{code}"
                ))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📍 **اختر ولايتك:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == 'new_search':
        # بحث جديد
        await start_from_callback(query)

async def get_weather(query, wilaya_name: str, location_name: str):
    """الحصول على معلومات الطقس من API"""
    
    # عرض رسالة انتظار
    await query.edit_message_text("⏳ جاري جلب معلومات الطقس...")
    
    try:
        # استدعاء API الطقس
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': f"{location_name},DZ",
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ar'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # استخراج المعلومات
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            wind_speed = data['wind']['speed']
            description = data['weather'][0]['description']
            
            # تحديد الأيقونة المناسبة
            weather_id = data['weather'][0]['id']
            icon = get_weather_icon(weather_id)
            
            # تنسيق الرسالة
            weather_text = f"""
{icon} **طقس {location_name}، {wilaya_name}** {icon}

📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
🕐 **الوقت:** {datetime.now().strftime('%H:%M')}

🌡️ **درجة الحرارة:** {temp}°C
🤚 **الشعور بـ:** {feels_like}°C
☁️ **الوصف:** {description}

💧 **الرطوبة:** {humidity}%
🌪️ **سرعة الرياح:** {wind_speed} م/ث
🔽 **الضغط الجوي:** {pressure} هيكتوباسكال
            """
            
            # زر بحث جديد
            keyboard = [[InlineKeyboardButton("🔍 بحث جديد", callback_data="new_search")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                weather_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        elif response.status_code == 404:
            await query.edit_message_text(
                f"❌ عذراً، لم أستطع إيجاد معلومات الطقس لـ {location_name}.\n\n"
                "جرب اختيار موقع آخر.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="back_to_wilayas")
                ]])
            )
        else:
            raise Exception(f"API Error: {response.status_code}")
    
    except requests.exceptions.Timeout:
        await query.edit_message_text(
            "⏱️ انتهت مهلة الطلب. يرجى المحاولة مرة أخرى.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 إعادة المحاولة", callback_data=f"daira_{wilaya_name}_{location_name}")
            ]])
        )
    
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        await query.edit_message_text(
            "❌ حدث خطأ أثناء جلب معلومات الطقس.\n\n"
            "يرجى التحقق من إعدادات API أو المحاولة لاحقاً.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_wilayas")
            ]])
        )

def get_weather_icon(weather_id: int) -> str:
    """الحصول على الأيقونة المناسبة حسب حالة الطقس"""
    if 200 <= weather_id < 300:
        return "⛈️"  # عواصف رعدية
    elif 300 <= weather_id < 400:
        return "🌦️"  # رذاذ
    elif 500 <= weather_id < 600:
        return "🌧️"  # مطر
    elif 600 <= weather_id < 700:
        return "❄️"  # ثلج
    elif 700 <= weather_id < 800:
        return "🌫️"  # ضباب/غبار
    elif weather_id == 800:
        return "☀️"  # صافي
    elif 801 <= weather_id < 900:
        return "☁️"  # غيوم
    else:
        return "🌤️"

async def start_from_callback(query):
    """بدء البوت من callback (بحث جديد)"""
    keyboard = []
    wilaya_items = list(WILAYAS.items())
    
    for i in range(0, len(wilaya_items), 4):
        row = []
        for code, name in wilaya_items[i:i+4]:
            row.append(InlineKeyboardButton(
                f"{name} ({code})",
                callback_data=f"wilaya_{code}"
            ))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌤️ **اختر ولايتك:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رسالة المساعدة"""
    help_text = """
📖 **دليل الاستخدام:**

1️⃣ اضغط /start لبدء البوت
2️⃣ اختر الولاية من القائمة
3️⃣ اختر الدائرة (إن وجدت)
4️⃣ احصل على معلومات الطقس الحالية

🔄 **الأوامر المتاحة:**
/start - بدء البوت
/help - عرض المساعدة

💡 **ملاحظة:** البيانات محدثة ومن مصادر موثوقة.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """تشغيل البوت"""
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # إضافة معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # بدء البوت
    logger.info("🚀 البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
