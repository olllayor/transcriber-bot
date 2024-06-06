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
    unique_filename = os.path.join(UPLOADS_DIRECTORY, str(uuid.uuid4()) + "." + file_ext)
    return unique_filename

@dp.message(CommandStart())
async def welcome_message(message: types.Message):
    await message.reply("Hi!!!\n\nSend video or music file")

@dp.message(F.content_type.in_({"audio", "video"}))
async def handle_audio_video(message: types.Message):
    try:
        # Check if the message has audio or video
        if message.content_type == types.ContentType.AUDIO:
            file_id = message.audio.file_id
            file_name = message.audio.file_name
            logging.info("Processing audio file...")
            processing_message = await message.reply("Processing audio file...")
        elif message.content_type == types.ContentType.VIDEO:
            file_id = message.video.file_id
            file_name = message.video.file_name
            logging.info("Processing video file...")
            processing_message = await message.reply("Processing video file...")
        else:
            await message.reply("Unsupported file format. Please send a supported audio or video file.")
            return

        # Get the actual file extension, handle cases where file_name might be None
        if file_name:
            file_ext = file_name.split(".")[-1].lower()
        else:
            await message.reply("Cannot process the file without a valid file name. Please try again with another file.")
            await processing_message.delete()
            return

        # Get file information
        file_info = await bot.get_file(file_id)

        logging.info(f"File size: {file_info.file_size} bytes")

        # Check if the file size is greater than 20MB (20 * 1024 * 1024 bytes)
        if file_info.file_size > 20 * 1024 * 1024:
            await message.reply("Please send a file that is smaller than 20MB.")
            await processing_message.delete()
            return

        # Generate a unique filename for the downloaded file
        unique_filename = generate_unique_filename(file_ext)

        # Download and save the file with the unique filename
        await bot.download_file(file_info.file_path, unique_filename)

        try:
            # Send the file to the admin using FSInputFile
            if message.content_type == types.ContentType.VIDEO:
                await bot.send_video(chat_id=ADMIN_USER_ID, video=FSInputFile(unique_filename))
            else:
                await bot.send_document(chat_id=ADMIN_USER_ID, document=FSInputFile(unique_filename))

            almost_done_message = await message.reply("Almost done...")
            # Transcribe audio using the 'whisper' library
            supported_audio_formats = ["wav", "mp3", "mp4", "m4a", "webm", "mov", "ogg"]
            if file_ext in supported_audio_formats:
                model = whisper.load_model("small")
                with NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    audio = AudioSegment.from_file(unique_filename, format=file_ext)
                    audio.export(temp_wav.name, format="wav")
                    result = model.transcribe(temp_wav.name)
                    
                    if result is None:
                        logging.error("Whisper transcription result is None.")
                        await message.reply("Transcription failed. The result is None. Please try again with another file.")
                        await processing_message.delete()
                        await almost_done_message.delete()
                        return

                    transcribed_text = result.get("text")
                    
                    if not transcribed_text:
                        logging.error("Transcribed text is empty or None.")
                        await message.reply("Error: Transcription failed. The transcribed text is empty.")
                        await processing_message.delete()
                        await almost_done_message.delete()
                        return

                    text_uz = translator.translate(transcribed_text, src="auto", dest="uz").text

                    # Combine transcribed_text and text_uz
                    combined_text = f"{transcribed_text}\n\n🇺🇿: {text_uz}"

                    # Check if the transcribed text is too long
                    if len(combined_text) > 4096:
                        await message.reply(combined_text[:4096])
                        await message.reply(combined_text[4096:])
                    else:
                        # Send the combined text as a single message
                        await message.reply(combined_text)

                    # Delete the processing and almost done messages
                    await processing_message.delete()
                    await almost_done_message.delete()
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

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        await message.reply(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    async def main():
        # Notify admin that the bot is running
        await on_start_notify_admin()
        # Start polling
        await dp.start_polling(bot)

    asyncio.run(main())
