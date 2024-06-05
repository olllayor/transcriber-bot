import logging
import os
import uuid
import asyncio
from tempfile import NamedTemporaryFile
from aiogram.types import FSInputFile
import whisper
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from googletrans import Translator
from pydub import AudioSegment

# Define the directory path where uploaded files will be saved
UPLOADS_DIRECTORY = "uploads"

# Ensure the uploads directory exists
os.makedirs(UPLOADS_DIRECTORY, exist_ok=True)
load_dotenv()

# Read environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

# Log the environment variables for debugging purposes
logging.basicConfig(level=logging.INFO)
logging.info(f"BOT_TOKEN: {BOT_TOKEN}")
logging.info(f"ADMIN_USER_ID: {ADMIN_USER_ID}")

# Check if BOT_TOKEN or ADMIN_USER_ID is empty
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the .env file")
if not ADMIN_USER_ID:
    raise ValueError("ADMIN_USER_ID is not set in the .env file")

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()  # Use MemoryStorage for in-memory state storage
dp = Dispatcher(bot=bot)

translator = Translator()


# Handler to send "Bot running" message to the admin
async def on_start_notify_admin():
    try:
        await bot.send_message(chat_id=ADMIN_USER_ID, text="Bot running")
    except Exception as e:
        logging.error(f"Error sending message to admin: {e}")


def generate_unique_filename(file_ext):
    unique_filename = os.path.join(
        UPLOADS_DIRECTORY, str(uuid.uuid4()) + "." + file_ext
    )
    return unique_filename


@dp.message(CommandStart())
async def welcome_message(message: types.Message):
    await message.reply("Hi!!!\n\nSend video or music file")


@dp.message(F.content_type.in_({"audio", "video"}))
async def handle_audio_video(message: types.Message):
    # Check if the message has audio or video
    if message.content_type == types.ContentType.AUDIO:
        file_id = message.audio.file_id
        file_ext = message.audio.file_name.split(".")[-1].lower()
        file_size = message.audio.file_size
        if file_size > 20 * 1024 * 1024:
            await message.reply("Please send a file that is smaller than 20MB.")
            return
        logging.info("Processing audio file...")
        await message.reply("Processing audio file...")
    elif message.content_type == types.ContentType.VIDEO:
        file_id = message.video.file_id
        file_ext = message.video.file_name.split(".")[-1].lower()
        file_size = message.video.file_size
        if file_size > 20 * 1024 * 1024:
            await message.reply("Please send a file that is smaller than 20MB.")
            return
        logging.info("Processing video file...")
        await message.reply("Processing video file...")
    else:
        await message.reply(
            "Unsupported file format. Please send a supported audio or video file."
        )
        return

    # Check if the file size is greater than 20MB (20 * 1024 * 1024 bytes)
    

    # Get file information
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    # Generate a unique filename for the downloaded file
    unique_filename = generate_unique_filename(file_ext)

    # Download and save the file with the unique filename
    await bot.download_file(file_path, unique_filename)

    try:
        # Send the file to the admin using FSInputFile or send video directly
        if message.content_type == types.ContentType.VIDEO:
            await bot.send_video(chat_id=ADMIN_USER_ID, video=FSInputFile(unique_filename))
        else:
            await bot.send_document(chat_id=ADMIN_USER_ID, document=FSInputFile(unique_filename))

        # Transcribe audio using the 'whisper' library
        supported_audio_formats = ["wav", "mp3", "mp4", "m4a", "webm", "mov", "ogg"]
        if file_ext in supported_audio_formats:
            model = whisper.load_model("base")
            with NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                audio = AudioSegment.from_file(unique_filename, format=file_ext)
                audio.export(temp_wav.name, format="wav")
                result = model.transcribe(temp_wav.name)
                transcribed_text = result["text"]
                text_uz = translator.translate(transcribed_text, src="auto", dest="uz").text

                # Combine transcribed_text and text_uz
                combined_text = f"{transcribed_text}\n\n🇺🇿: {text_uz}"

                # Split the message if it exceeds 4096 characters
                max_length = 4096
                for i in range(0, len(combined_text), max_length):
                    await message.reply(combined_text[i:i+max_length])

        else:
            await message.reply(f"Audio format {file_ext} is not currently supported for transcription.")
    except Exception as e:
        logging.error(f"Error processing the audio: {str(e)}")
        await message.reply(f"Error processing the audio: {str(e)}")
    finally:
        # Remove the file to clear storage
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

        # Remove the temporary wav file if it exists
        wav_file = os.path.join(UPLOADS_DIRECTORY, "input_audio.wav")
        if os.path.exists(wav_file):
            os.remove(wav_file)


if __name__ == "__main__":
    async def main():
        # Notify admin that the bot is running
        await on_start_notify_admin()
        # Start polling
        await dp.start_polling(bot)

    asyncio.run(main())
