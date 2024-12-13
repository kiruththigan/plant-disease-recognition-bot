from dotenv import load_dotenv
import os
import logging
import time
import requests
from telegram import Update, ForceReply
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
CHAT_API_URL = os.getenv("CHAT_API_URL")

chat_history = {}


# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_history[user.id] = []
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to the Plant Care AI Assistant bot!",
        reply_markup=ForceReply(selective=True),
    )


# Help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Send an image of a plant, and I'll try to recognize its disease!"
    )


# Chat with ai
async def handle_chat(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        if user.id not in chat_history:
            chat_history[user.id] = []

        message = {
            "id": str(int(time.time() * 1000)),
            "role": "user",
            "content": update.message.text,
        }
        chat_history[user.id].append(message)

        data = {
            "model": "plant-care",
            "messages": chat_history[user.id],
            "stream": False,
        }

        if user.id in chat_history:
            # Print the chat history for the specific user
            for message in chat_history[user.id]:
                print("################################")
                print(f"Message ID: {message['id']}")
                print(f"Role: {message['role']}")
                print(f"Content: {message['content']}")
                print("------")
                print("################################")

        response = requests.post(CHAT_API_URL, json=data)
        if response.status_code == 200:
            result = response.json()

            responseMessage = {
                "id": str(int(time.time() * 1000)),
                "role": "assistant",
                "content": result["message"]["content"],
            }

            chat_history[user.id].append(responseMessage)
            response_text = result["message"]["content"]
        else:
            response_text = "Sorry, I couldn't reply. Please try again."

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while contacting AI: {e}")
        response_text = "Sorry, there was an error with the chat service."

    await update.message.reply_text(response_text)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()

    contents = await photo_file.download_as_bytearray()

    try:
        response = requests.post(API_URL, files={"file": contents})

        if response.status_code == 200:
            prediction_data = response.json()
            prediction_text = f"Prediction: {prediction_data['prediction']}"
            promt = f"You are Plant Care AI Assistant, an expert in agriculture and plant diseases. A user has recently identified {prediction_data['prediction']} in their plant. Provide detailed information about this disease, its causes, symptoms, prevention, and treatment methods. Also, be prepared to answer follow-up questions about this disease and other plant care issues."
            message = {
                "id": str(int(time.time() * 1000)),
                "role": "system",
                "content": promt,
            }

            chat_history[user.id] = [message]
            # chat_history[user.id].append(message)
        else:
            prediction_text = "Sorry, I couldn't predict the disease. Please try again."

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while contacting FastAPI: {e}")
        prediction_text = "Sorry, there was an error with the prediction service."

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=prediction_text
    )


def main():

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    logger.info("Starting Telegram bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
