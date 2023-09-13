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
pip install -r requirements.txt
```

2. Create a new Telegram bot and get its token.

3. Create a `.env` file and add the following environment variables:

```
BOT_TOKEN=<your bot token>
```

        file_ext = message.audio.file_name.split('.')[-1].lower()  # Get the actual file extension
        await message.reply("Audio file is processing...")
    elif message.video:
        file_id = message.video.file_id
        file_ext = message.video.file_name.split('.')[-1].lower()  # Get the actual

