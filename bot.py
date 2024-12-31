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
log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'
logging.basicConfig(
    filename=log_filename,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram and Mistral API credentials
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
ADMINS = list(map(int, os.getenv('ADMINS').split(',')))
MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'

# Initial prompt for slang, jaksel, and betawi
INITIAL_PROMPT = (
    "Always respond in indonesian slang, gaul, jaksel or betawi for this "
    "Example: 'Etdah, gak bisa gitu cing. Cuy, gue tuh yang paling experienced disini if we are talking about coding.' "
    "Do not use formal indonesian language or pure english."
    "Respond to messages from the user in the same language style. Heavily use jaksel tone, indonesian-english in slang"
)

# Welcome message when the bot joins a group
async def group_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Wassup gengss, kenalin gue sarmili, orang yang paling smart people')

# Variables to store the message count
message_count = 0  # Initialize message count
last_message = ""  # Variable to store the last message

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_message, message_count
    user_message = update.message.text

    # Update the last message and message count
    last_message = user_message
    message_count += 1

    # Check if the message is from a private chat
    if update.message.chat.type == 'private':
        if not is_admin(update.effective_user.id):
            await update.message.reply_text('Etdah, sapa lu cing? berani bener DM DM gue. Gue laporin bokap gue liat aja lu. Bokap gw polwan!')
            return

    # Check if the bot is mentioned
    bot_mentioned = is_bot_mentioned(user_message, context.bot.username)

    # Check if the message is a reply to a bot message
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id

    # Allow response if the bot is mentioned or if the message is a reply to the bot
    if bot_mentioned or is_reply_to_bot:
        logger.info("Bot mentioned or replying to bot. Processing message.")
        full_prompt = f"{INITIAL_PROMPT} User: {user_message}"
        response = get_mistral_response(full_prompt)
        await update.message.reply_text(response)

    # Respond to the last message after every 5 messages
    if message_count % 5 == 0:
        logger.info("Detected 5 messages in the group. Responding with the last message.")
        context_prompt = f"{INITIAL_PROMPT} Context: {last_message}"
        context_response = get_mistral_response(context_prompt)
        await update.message.reply_text(context_response)

    # Suppress logging and return if the bot is not mentioned
    if not bot_mentioned:
        return

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_bot_mentioned(message_text: str, bot_username: str) -> bool:
    # Check if the bot's username is mentioned in the message text
    mention = f"@{bot_username}"
    if mention in message_text:
        logger.info(f"Bot mentioned in message: {message_text}")
        return True
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
    #application.add_handler(CommandHandler("start", start))  # Optional: Keep if you want to handle /start command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_joined))

    application.run_polling()

if __name__ == '__main__':
    main()
