import os
import json
import requests
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# लॉगिंग सेटअप
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# .env से टोकन और एडमिन आईडी लोड करें
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# डेटा स्टोरेज फ़ाइल
DATA_FILE = "user_data.json"

# ग्लोबल वेरिएबल्स
user_data = {}
redeem_codes = {}
live_member_count = 0

# डेटा लोड करने का फंक्शन
def load_data():
    global user_data, live_member_count
    try:
        with open(DATA_FILE, "r") as file:
            user_data = json.load(file)
            live_member_count = len(user_data)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}

# डेटा सेव करने का फंक्शन
def save_data():
    with open(DATA_FILE, "w") as file:
        json.dump(user_data, file)

# स्टार्ट कमांड
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global live_member_count
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    args = context.args

    referrer_id = args[0].replace("Bot", "") if args else None
    if referrer_id and int(referrer_id) != user_id and user_id not in user_data:
        user_data[user_id] = {'credits': 3, 'referrer': int(referrer_id)}
        user_data[int(referrer_id)]['credits'] += 1
        await context.bot.send_message(int(referrer_id), "🎉 कोई आपके लिंक से जॉइन हुआ! +1 क्रेडिट मिला 💰")

    if user_id not in user_data:
        user_data[user_id] = {'credits': 3, 'referrer': None}
        live_member_count += 1
        save_data()

    invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
    welcome_msg = f"👋 Welcome, {user_name} 🎉\n\n💡 Explore the bot options below.\n__________________________"

    keyboard = [
        [InlineKeyboardButton("🐍 WORM GPT 🐍", callback_data="worm_gpt"),
         InlineKeyboardButton("💰 CREDIT 💰", callback_data="credit")],
        [InlineKeyboardButton("🔥 DEV 🔥", url="https://t.me/GOAT_NG")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

# बटन हैंडलर
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "worm_gpt":
        keyboard = [[InlineKeyboardButton("BACK", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💬 अपनी क्वेरी नीचे टाइप करें:", reply_markup=reply_markup)

    elif query.data == "credit":
        credits = user_data.get(user_id, {}).get("credits", 0)
        invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
        message = f"💰 आपके पास {credits} क्रेडिट्स हैं।\n📊 कुल सदस्य: {live_member_count}\n\n" \
                  f"🎉 और क्रेडिट्स पाने के लिए अपने दोस्तों को इनवाइट करें!\n\n" \
                  f"🔗 [क्लिक करें]({invite_link})"
        keyboard = [[InlineKeyboardButton("BACK", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🐍 WORM GPT 🐍", callback_data="worm_gpt"),
             InlineKeyboardButton("💰 CREDIT 💰", callback_data="credit")],
            [InlineKeyboardButton("🔥 DEV 🔥", url="https://t.me/GOAT_NG")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💡 मेनू में वापस। एक विकल्प चुनें:", reply_markup=reply_markup)

# यूजर मेसेज हैंडलर
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_data.get(user_id, {}).get("credits", 0) > 0:
        try:
            response = requests.get(f"https://ngyt777gworm.tiiny.io/?question={text}")
            answer = response.text.strip()

            user_data[user_id]['credits'] -= 1
            save_data()

            await update.message.reply_text(f"💡 *Answer* 💡 \n\n{answer}", parse_mode="Markdown")

        except Exception as e:
            logging.error(f"Error fetching response: {e}")
            await update.message.reply_text("❌ कुछ गड़बड़ हो गई, कृपया फिर से प्रयास करें।")

    else:
        invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
        await update.message.reply_text(f"⚠️ आपके पास कोई क्रेडिट नहीं बचा।\n\n"
                                        f"🎉 इनवाइट करके और क्रेडिट्स पाएं!\n\n"
                                        f"🔗 [क्लिक करें]({invite_link})",
                                        parse_mode="Markdown")

# एडमिन द्वारा रिडीम कोड जनरेट करना
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ आपको इस कमांड का उपयोग करने की अनुमति नहीं है।")
        return

    try:
        code, value = context.args[0], int(context.args[1])
        redeem_codes[code] = value
        await update.message.reply_text(f"✅ कोड `{code}` {value} क्रेडिट्स के लिए तैयार!", parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ गलत फ़ॉर्मेट! उपयोग करें: `/redeem <code> <value>`")

# यूजर द्वारा रिडीम कोड उपयोग करना
async def handle_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        code = context.args[0]
        if code in redeem_codes:
            user_data[user_id]['credits'] += redeem_codes.pop(code)
            save_data()
            await update.message.reply_text("✅ रिडीम सफल!")
        else:
            await update.message.reply_text("❌ कोड अमान्य है।")
    except IndexError:
        await update.message.reply_text("❌ कृपया एक रिडीम कोड प्रदान करें।")

# बॉट रन करना
def main():
    load_data()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
