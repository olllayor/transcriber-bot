import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
import warnings
from pydub import AudioSegment
import whisper
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from pydub.exceptions import PydubException
from googletrans import Translator
import uuid

# Define the directory path where uploaded files will be saved
UPLOADS_DIRECTORY = "uploads"

# Ensure the uploads directory exists
os.makedirs(UPLOADS_DIRECTORY, exist_ok=True)
load_dotenv()
ADMIN_USER_ID =os.getenv("ADMIN_USER_ID")
# Function to generate a unique filename
# Check if ADMIN_USER_ID is empty
if not ADMIN_USER_ID:
    raise ValueError("ADMIN_USER_ID is not set in the .env file")

bot = Bot(token=os.getenv("BOT_TOKEN"))
# Configure the logging
dp = Dispatcher(bot)
translator = Translator()
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
warnings.filterwarnings('ignore')
# Initialize the bot

# Handler to send "Bot running" message to the admin
async def on_start_notify_admin(dp):
    try:
        await bot.send_message(chat_id=ADMIN_USER_ID, text="Bot running")
    except Exception as e:
        logging.error(f"Error sending message to admin: {e}")
def generate_unique_filename(file_ext):
    unique_filename = os.path.join(UPLOADS_DIRECTORY, str(uuid.uuid4()) + "." + file_ext)
    return unique_filename

@dp.message_handler(commands=["start"])
async def handle_audio_video(message: types.Message):
    await message.reply("Hi!!!\n\nSend video or music file")

@dp.message_handler(content_types={types.ContentType.AUDIO, types.ContentType.VIDEO})
async def handle_audio_video(message: types.Message):
    # Check if the message has audio or video
    if message.audio:
        file_id = message.audio.file_id
        file_ext = message.audio.file_name.split('.')[-1].lower()  # Get the actual file extension
        await message.reply("Audio file is processing...")
    elif message.video:
        file_id = message.video.file_id
        file_ext = message.video.file_name.split('.')[-1].lower()  # Get the actual file extension
        await message.reply("Video file is processing...")
    else:
        await message.reply("Unsupported file format. Please send a supported audio or video file.")
        return

    # Download the file
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    # Generate a unique filename for the downloaded file
    unique_filename = generate_unique_filename(file_ext)

    # Check if the file size is greater than 20MB (20 * 1024 * 1024 bytes)
    if file_info.file_size > 20 * 1024 * 1024:
        await message.reply("Please send a file that is smaller than 20MB.")
        return

    # Download and save the file with the unique filename
    await bot.download_file(file_path, unique_filename)

    try:
        # Transcribe audio using the 'whisper' library
        if file_ext in ["wav", "mp3", "mp4", "m4a", "webm", "mov", "ogg"]:
            model = whisper.load_model("small")
            audio = AudioSegment.from_file(unique_filename, format=file_ext)
            audio.export(os.path.join(UPLOADS_DIRECTORY, "input_audio.wav"), format="wav")
            result = model.transcribe(os.path.join(UPLOADS_DIRECTORY, "input_audio.wav"))
            transcribed_text = result["text"]
            text_uz = translator.translate(transcribed_text, src='auto', dest='uz').text

            # Combine transcribed_text and text_uz
            combined_text = f"{transcribed_text}\n\n🇺🇿: {text_uz}"

            # Check if the combined text is too long
            if len(combined_text) > 4096:
                if len(transcribed_text) < 4096:
                    await message.reply(transcribed_text)
                else:
                    await message.reply("Transcribed Text is too long for Telegram's max message length")
            else:
                # Send the combined text as a single message
                await message.reply(combined_text)
        else:
            await message.reply("Unsupported file format. Please send a supported audio or video file.")
    except PydubException as e:
        await message.reply(f"Error processing the audio: {str(e)}")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_notify_admin)
