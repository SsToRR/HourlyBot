# Hourly Check Bot для Microsoft Teams

Бот для Microsoft Teams, который отправляет пользователям вопросы о том, что они делают в определенные часы дня и создает AI-обобщения их активности.

## 🚀 Возможности

- **Ежечасные вопросы**: Бот автоматически спрашивает пользователей о их активности каждые 30 минут с 9:00 до 17:00
- **AI-обобщения**: Использует OpenAI GPT для создания кратких обобщений активности за день
- **Интеграция с Teams**: Полная интеграция с Microsoft Teams через Bot Framework
- **Планировщик задач**: Использует Celery для планирования и выполнения задач
- **База данных**: Хранит ответы пользователей и настройки в PostgreSQL

## 📋 Требования

- Python 3.8+
- PostgreSQL
- Redis
- Microsoft Bot Framework аккаунт
- OpenAI API ключ
- Ngrok (для локальной разработки)

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone <your-repository-url>
cd Hourlybot
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
cd mybot
pip install -r requirements.txt
```

### 4. Настройка базы данных
```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя (опционально)
python manage.py createsuperuser
```

### 5. Настройка переменных окружения
Создайте файл `.env` в папке `mybot/`:
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# База данных
POSTGRES_DB=hourlybot_db
POSTGRES_USER=hourlybot_user
POSTGRES_PASSWORD=hourlybot_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Bot Framework
BOT_FRAMEWORK_APP_ID=your-app-id
BOT_FRAMEWORK_APP_PASSWORD=your-app-password

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 6. Настройка Ngrok
1. Скачайте ngrok с [ngrok.com](https://ngrok.com)
2. Запустите ngrok:
```bash
ngrok http 8000
```
3. Обновите URL в файлах `Bot.bot` и `manifest/manifest.json`

## 🚀 Запуск

### 1. Запуск Redis
```bash
redis-server
```

### 2. Запуск Django сервера
```bash
python manage.py runserver
```

### 3. Запуск Celery worker
```bash
celery -A bot1 worker --loglevel=info
```

### 4. Запуск Celery beat (планировщик)
```bash
celery -A bot1 beat --loglevel=info
```

### Альтернативно, используйте скрипт для запуска всех сервисов:
```bash
python start_celery.py
```

## 📱 Настройка Teams Bot

### 1. Регистрация в Bot Framework
1. Перейдите на [Bot Framework Portal](https://dev.botframework.com/)
2. Создайте новый бот
3. Получите App ID и App Password

### 2. Обновление конфигурации
Обновите следующие файлы с вашими данными:
- `Bot.bot` - конфигурация бота
- `manifest/manifest.json` - манифест Teams приложения
- `mybot/bot1/settings.py` - настройки Django

### 3. Загрузка в Teams
1. Используйте Teams App Studio для загрузки манифеста
2. Или загрузите манифест вручную через Teams Developer Portal

## 📊 Использование

### Команды бота:
- `start` - Подписаться на ежечасные вопросы
- `stop` - Отписаться от вопросов

### Время вопросов:
Бот задает вопросы в следующие часы:
- 9:00, 9:30, 10:00, 10:30, 11:00, 11:30
- 12:00, 12:30, 14:00, 14:30, 15:00, 15:30
- 16:00, 16:30, 17:00

### AI-обобщения:
В 17:00 бот автоматически создает и отправляет AI-обобщение активности за день.

## 🏗️ Структура проекта

```
Hourlybot/
├── Bot.bot                 # Конфигурация Bot Framework
├── manifest/               # Манифест Teams приложения
│   ├── manifest.json
│   └── README.md
├── mybot/                  # Основное Django приложение
│   ├── bot1/              # Django проект
│   │   ├── settings.py    # Настройки Django
│   │   ├── urls.py        # URL конфигурация
│   │   └── celery.py      # Конфигурация Celery
│   ├── bot2/              # Django приложение бота
│   │   ├── models.py      # Модели данных
│   │   ├── views.py       # HTTP обработчики
│   │   ├── bot_handler.py # Логика бота
│   │   └── tasks.py       # Celery задачи
│   ├── requirements.txt   # Зависимости Python
│   ├── manage.py          # Django management
│   └── start_celery.py    # Скрипт запуска
└── README.md              # Этот файл
```

## 🔧 Разработка

### Добавление новых задач
1. Создайте новую задачу в `bot2/tasks.py`
2. Настройте расписание в Django admin или через код
3. Перезапустите Celery beat

### Изменение времени вопросов
Отредактируйте список `question_times` в `bot2/bot_handler.py`

### Добавление новых команд
Добавьте обработку новых команд в метод `on_message_activity` в `bot2/bot_handler.py`

## 🐛 Устранение неполадок

### Бот не отвечает
1. Проверьте, что ngrok запущен и URL актуален
2. Убедитесь, что все сервисы запущены
3. Проверьте логи в `bot.log`

### Ошибки Celery
1. Убедитесь, что Redis запущен
2. Проверьте настройки в `settings.py`
3. Перезапустите Celery worker и beat

### Проблемы с базой данных
1. Проверьте подключение к PostgreSQL
2. Убедитесь, что миграции применены
3. Проверьте переменные окружения

## 📝 Лицензия

Этот проект создан для внутреннего использования.

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

При возникновении проблем создайте Issue в репозитории или обратитесь к разработчику. 