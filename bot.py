import os
import requests
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging to output to a date-based log file
log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'  # Create log filename based on current date
logging.basicConfig(
    filename=log_filename,  # Log to this file
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram and Mistral API credentials
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'

# List of admin UIDs
ADMINS = list(map(int, os.getenv('ADMINS').split(',')))  # Update to support multiple admin IDs

# Initial prompt for slang, jaksel, and betawi
INITIAL_PROMPT = (
    "Always respond in indonesian slang, gaul, jaksel or betawi for this "
    "Example: 'Etdah, gak bisa gitu cing. Hello, gue tuh yang paling experienced disini, elo sape?.' "
    "Do not use formal indonesian language or pure english. "
    "Respond to messages from the user in the same language style."
)

# Variables to store the last message and message count
last_message = None
message_count = 0

# Bot activation status
bot_activated = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global bot_activated
    if is_admin(update.effective_user.id):
        bot_activated = True
        await update.message.reply_text('Wassup gengss, kenalin gue sarmili, orang yang paling smart people')
    else:
        await update.message.reply_text('Sorry, only admins can use this command.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_message, message_count
    if not bot_activated:
        logger.info("Bot is not activated. Ignoring message.")
        return

    user_message = update.message.text

    # Update the last message and message count
    last_message = user_message
    message_count += 1

    # Log the message and its entities
    logger.info(f"Received message: {user_message}")
    logger.info(f"Message entities: {update.message.entities}")

    # Check if the message is from a private chat
    if update.message.chat.type == 'private':
        if not is_admin(update.effective_user.id):
            await update.message.reply_text('Etdah, sapa lu cing? berani bener DM DM gue. Gue laporin bokap gue liat aja lu. Bokap gw polwan!')
            logger.info(f"Blocked private message from non-admin user: {update.effective_user.id}")
            return

    # Check if the bot is mentioned
    bot_mentioned = is_bot_mentioned(user_message, context.bot.username)
    logger.info(f"Is bot mentioned: {bot_mentioned}")

    # Check if the message is a reply to a bot message
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    logger.info(f"Is reply to bot: {is_reply_to_bot}")

    # Allow response if the bot is mentioned or if the message is a reply to the bot
    if bot_mentioned or is_reply_to_bot:
        logger.info("Bot mentioned or replying to bot. Processing message.")
        full_prompt = f"{INITIAL_PROMPT} User: {user_message}"
        response = get_mistral_response(full_prompt)
        await update.message.reply_text(response)
    else:
        logger.info(f"Bot not mentioned in message: {user_message}")

async def group_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Wassup gengss, kenalin gue sarmili, orang yang paling smart people')

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_bot_mentioned(message_text: str, bot_username: str) -> bool:
    # Check if the bot's username is mentioned in the message text
    mention = f"@{bot_username}"
    if mention in message_text:
        logger.info(f"Bot mentioned in message: {message_text}")
        return True
    logger.info(f"Bot not mentioned in message: {message_text}")
    return False

def get_mistral_response(prompt: str) -> str:
    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'mistral-large-latest',
        'messages': [{'role': 'user', 'content': prompt}]
    }

    response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        logger.info(response.json())  # Log the response for debugging
        return response.json()['choices'][0]['message']['content']
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")  # Log the error for debugging
        return 'Maaf, terjadi kesalahan. Coba lagi nanti.'

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_joined))

    application.run_polling()

if __name__ == '__main__':
    main()
