import sqlite3
from telegram import Update
from telegram.ext import (
    MessageHandler, 
    CommandHandler,  
    ConversationHandler,
    filters, 
    ContextTypes, 
    Application
)

TOKEN = ""
ADMIN_UUIDS = [] # STORE AS INTS STATICLY


connection = sqlite3.connect("database.db")
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users
(uuid TEXT PRIMARY KEY, uname TEXT, fname TEXT, lname TEXT)
''')
connection.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uuid = update.message.chat.id
    uname = update.message.chat.username
    fname = update.message.chat.first_name
    lname = update.message.chat.last_name

    # check for dup enteries
    cursor.execute('SELECT * FROM users WHERE uuid = (?)', (uuid, ))
    existing_user = cursor.fetchone()

    if existing_user is None:
        cursor.execute('''
        INSERT INTO users (uuid, uname, fname, lname) VALUES (?, ?, ?, ?) 
        ''', (uuid, uname, fname, lname))
        connection.commit()
        await update.effective_message.reply_text("شما در لیست ربات اخبار قرار گرفته اید")
    
    else:
        await update.effective_message.reply_text("شما قبلا در لیست ربات اخبار قرار گرفته شده بودید")

BROADCAST = range(1)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id not in ADMIN_UUIDS:
        return ConversationHandler.END
    
    await update.effective_message.reply_text("لطفا اخبار خود را ارسال کنید تا برای مخاطبان ارسال شود اگر نمیخواید مطلبی ارسال کنید از /cancel استفاده کنید")

    return BROADCAST

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT uuid FROM users')
    all_users = cursor.fetchall()

    for (uuid, ) in all_users:
        try: 
            if update.message.text:
                await context.bot.send_message(chat_id=uuid, text=update.message.text)

            elif update.message.photo:
                await context.bot.send_photo(chat_id=uuid, photo=update.message.photo[-1].file_id)

            elif update.message.video:
                await context.bot.send_video(chat_id=uuid, video=update.message.video.file_id)

            elif update.message.document:
                await context.bot.send_document(chat_id=uuid, document=update.message.document.file_id)

            elif update.message.location:
                await context.bot.send_location(chat_id=uuid, latitude=update.message.location.latitude, longitude=update.message.location.longitude)

            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=uuid, sticker=update.message.sticker.file_id)

            elif update.message.animation:
                await context.bot.send_animation(chat_id=uuid, animation=update.message.animation.file_id)

            elif update.message.audio:
                await context.bot.send_audio(chat_id=uuid, audio=update.message.audio.file_id)

            elif update.message.voice:
                await context.bot.send_voice(chat_id=uuid, voice=update.message.voice.file_id)

            else:
                await update.message.reply_text("این نوع پیام پشتیبانی نمی‌شود.")

        except Exception as e:
            print(f"Could not send to {uuid}: {e}")

    await update.effective_message.reply_text("پیام شما برای مخاطبان ارسال گشت")
    return ConversationHandler.END
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("پیام لغو شد")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, do_broadcast)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handlers([
        CommandHandler("start", start),
        conv_handler
    ])

    print("bot started")
    app.run_polling()

if __name__ == "__main__":
    main()