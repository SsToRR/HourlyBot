# Microsoft Teams Bot - Daily Check

A Django-based Microsoft Teams bot that sends "What are you doing right now?" to users every day at 11:30 AM.

## Features

- Sends daily questions at 11:30 AM
- Stores user responses in database
- Works with Bot Framework Emulator for testing
- Scheduled tasks using Celery
- Cleanup of old responses

## Setup Instructions

### Option 1: Docker (Recommended)

The easiest way to run the bot is using Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This will start:
- Django web server on port 8000
- Redis server
- Celery worker
- Celery beat scheduler

### Option 2: Local Development

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Install Redis (Required for Celery)

**Windows:**
- Download Redis from https://github.com/microsoftarchive/redis/releases
- Or use WSL2 with Redis

**macOS:**
```bash
brew install redis
```

**Linux:**
```bash
sudo apt-get install redis-server
```

#### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 4. Start Redis Server

```bash
redis-server
```

#### 5. Start Celery Worker (in a new terminal)

```bash
celery -A bot1 worker --loglevel=info
```

#### 6. Start Celery Beat (in another new terminal)

```bash
celery -A bot1 beat --loglevel=info
```

#### 7. Start Django Server

```bash
python manage.py runserver
```

## Testing with Bot Framework Emulator

1. Download and install [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)

2. Open Bot Framework Emulator

3. Set the bot URL to:
   ```
   http://localhost:8000/bot/api/messages
   ```

4. Leave the Microsoft App ID and Microsoft App Password fields empty (for emulator testing)

5. Click "Connect"

6. Start a conversation and test the bot

## Docker Commands

```bash
# Start all services
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Restart a specific service
docker-compose restart web

# Rebuild and restart
docker-compose up --build --force-recreate
```

## Bot Endpoints

- `POST /bot/api/messages` - Main bot endpoint
- `GET /bot/api/health` - Health check
- `POST /bot/api/proactive` - Send proactive messages

## Scheduled Tasks

- **Daily Question**: Runs every day at 11:30 AM
- **Cleanup**: Removes responses older than 30 days (runs daily at midnight)

## Database Models

- `TeamsUser`: Stores user information
- `UserResponse`: Stores user responses to questions

## Configuration

The bot is configured for emulator testing with no authentication. For production:

1. Set `BOT_FRAMEWORK_APP_ID` and `BOT_FRAMEWORK_APP_PASSWORD` in settings
2. Configure proper authentication
3. Set up ngrok or similar for external access

## Troubleshooting

1. **500 Errors**: Check Django logs for detailed error messages
2. **Celery Issues**: Ensure Redis is running
3. **Bot Not Responding**: Check if all services are running (Django, Celery worker, Celery beat)
4. **Scheduled Tasks Not Running**: Verify Celery beat is running and check the schedule configuration

## Development

To modify the bot behavior:
- Edit `bot2/bot_handler.py` for message handling logic
- Edit `bot2/tasks.py` for scheduled task logic
- Edit `bot1/celery.py` for task scheduling 