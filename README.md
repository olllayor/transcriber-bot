 # Audio and Video Transcription Bot

This bot can transcribe audio and video files sent by users. It uses the whisper library for transcription and the googletrans library for translation.

## Prerequisites

- Python 3.6 or later
- aiogram
- pydub
- whisper
- googletrans
- ffmpeg (for video transcription)

## Setup

1. Create a new Python project and install the required dependencies.

```
python -m venv venv
source venv/bin/activate
pip install aiogram pydub whisper googletrans
```

2. Create a new Telegram bot and get its token.

3. Create a `.env` file and add the following environment variables:

```
BOT_TOKEN=<your bot token>
```

4. Create a new file called `bot.py` and paste the following code:

```python
import logging

import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
import warnings
from pydub import AudioSegment
import whisper
from pydub.exceptions import PydubException
from googletrans import Translator
# from supabase import create_database
load_dotenv()
# Configure the logging
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore')
# Initialize the bot
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)
translator = Translator()


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
        file_ext = message.video.file_name.split('.')[-1].lower()  # Get the actual

