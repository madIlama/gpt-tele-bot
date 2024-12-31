# Use a minimal Alpine image
FROM python:3.11-alpine
# Set the working directory
WORKDIR /app
# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy the application code
COPY . .
# Copy the .env file
COPY .env ./
# Command to run the bot
CMD ["python", "bot.py"]
