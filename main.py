import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from googletrans import Translator, LANGUAGES

# تنظیم لاگ
logging.basicConfig(
    filename="translatebotlog.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)

# تنظیم متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# بررسی وجود متغیرها
if not all([BOT_TOKEN, API_ID, API_HASH]):
    LOGGER.error("Missing environment variables. Please set BOT_TOKEN, API_ID, and API_HASH.")
    raise ValueError("Missing environment variables.")

# ایجاد نمونه ربات
app = Client(
    name="translate_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=10
)

# ایجاد شیء مترجم
translator = Translator()

# دستور /start
@app.on_message(filters.command(["start"]) & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        f"سلام {message.from_user.first_name}!\n\n"
        "من یک ربات ترجمه هستم. می‌توانم متن شما را به زبان‌های مختلف ترجمه کنم.\n\n"
        "دستورات:\n"
        "- /translate: شروع ترجمه\n"
        "- /languages: نمایش لیست زبان‌های پشتیبانی‌شده\n\n"
        "برای شروع، از /translate استفاده کنید!",
        quote=True
    )
    LOGGER.info(f"User {message.from_user.id} started the bot.")

# دستور /languages
@app.on_message(filters.command(["languages"]) & filters.private)
async def languages_handler(client: Client, message: Message):
    lang_list = "\n".join([f"{code}: {name}" for code, name in LANGUAGES.items()])
    await message.reply_text(
        f"زبان‌های پشتیبانی‌شده:\n\n{lang_list}\n\n"
        "برای ترجمه، از /translate استفاده کنید و کد زبان (مثل 'en' برای انگلیسی) را وارد کنید.",
        quote=True
    )
    LOGGER.info(f"User {message.from_user.id} requested language list.")

# دستور /translate
@app.on_message(filters.command(["translate"]) & filters.private)
async def translate_handler(client: Client, message: Message):
    # دکمه‌های انتخاب زبان‌های پراستفاده
    buttons = [
        [
            InlineKeyboardButton("انگلیسی (en)", callback_data="lang_en"),
            InlineKeyboardButton("فارسی (fa)", callback_data="lang_fa"),
        ],
        [
            InlineKeyboardButton("عربی (ar)", callback_data="lang_ar"),
            InlineKeyboardButton("فرانسه (fr)", callback_data="lang_fr"),
        ],
        [
            InlineKeyboardButton("آلمانی (de)", callback_data="lang_de"),
            InlineKeyboardButton("اسپانیایی (es)", callback_data="lang_es"),
        ],
        [
            InlineKeyboardButton("زبان دیگر", callback_data="lang_custom"),
            InlineKeyboardButton("لغو", callback_data="cancel")
        ]
    ]
    await message.reply_text(
        "لطفاً زبان مقصد را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )
    LOGGER.info(f"User {message.from_user.id} started translation process.")

# مدیریت انتخاب زبان
@app.on_callback_query(filters.regex(r"^lang_"))
async def lang_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    lang_code = callback_query.data.split("_")[1]
    
    if lang_code == "custom":
        msg = await callback_query.message.reply_text(
            "لطفاً کد زبان مقصد (مثل 'en' برای انگلیسی) را وارد کنید:",
            quote=True
        )
        # استفاده از pyromod برای دریافت پاسخ کاربر
        try:
            response = await client.listen.Message(filters.text & filters.user(user_id), timeout=60)
            lang_code = response.text.strip()
            if lang_code not in LANGUAGES:
                await response.reply_text("کد زبان نامعتبر است. از /languages برای مشاهده لیست استفاده کنید.", quote=True)
                LOGGER.warning(f"User {user_id} entered invalid language code: {lang_code}")
                return
        except TimeoutError:
            await msg.edit_text("زمان پاسخ تمام شد. لطفاً دوباره /translate را اجرا کنید.")
            LOGGER.warning(f"User {user_id} timed out while entering custom language.")
            return
    else:
        await callback_query.message.edit_text(f"زبان انتخاب‌شده: {LANGUAGES[lang_code]}\nلطفاً متن خود را برای ترجمه وارد کنید:")
        try:
            response = await client.listen.Message(filters.text & filters.user(user_id), timeout=60)
            text = response.text.strip()
        except TimeoutError:
            await callback_query.message.edit_text("زمان پاسخ تمام شد. لطفاً دوباره /translate را اجرا کنید.")
            LOGGER.warning(f"User {user_id} timed out while entering text.")
            return
    
    # انجام ترجمه
    try:
        translated = translator.translate(text, dest=lang_code)
        await response.reply_text(
            f"**متن اصلی**: {text}\n"
            f"**زبان مقصد**: {LANGUAGES[lang_code]}\n"
            f"**ترجمه**: {translated.text}",
            quote=True
        )
        LOGGER.info(f"User {user_id} translated text to {lang_code}: {translated.text}")
    except Exception as e:
        await response.reply_text("خطا در ترجمه. لطفاً دوباره امتحان کنید.", quote=True)
        LOGGER.error(f"Translation error for user {user_id}: {str(e)}")

# مدیریت دکمه لغو
@app.on_callback_query(filters.regex(r"^cancel"))
async def cancel_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("عملیات ترجمه لغو شد. از /translate برای شروع دوباره استفاده کنید.")
    LOGGER.info(f"User {callback_query.from_user.id} canceled translation.")

# اجرای ربات
if __name__ == "__main__":
    LOGGER.info("Starting Translate Bot...")
    app.run()
