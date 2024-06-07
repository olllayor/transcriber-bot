# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Copy the rest of the application code into the container
COPY . .

# Command to run the bot
CMD ["python", "bot.py"]
