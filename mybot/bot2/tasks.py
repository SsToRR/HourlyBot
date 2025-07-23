import logging
from datetime import datetime, time, timedelta
from django.utils import timezone
from celery import shared_task
from .models import TeamsUser, UserResponse
import pytz
from django.conf import settings
import json
import requests
import openai

logger = logging.getLogger(__name__)

def get_kazakhstan_time():
    """Get current time in Kazakhstan timezone"""
    kazakhstan_tz = pytz.timezone('Asia/Almaty')
    return timezone.now().astimezone(kazakhstan_tz)

def get_access_token():
    """Get access token from Microsoft"""
    try:
        token_url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': settings.BOT_FRAMEWORK_APP_ID,
            'client_secret': settings.BOT_FRAMEWORK_APP_PASSWORD,
            'scope': 'https://api.botframework.com/.default'
        }
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()['access_token']
        logger.error(f"Не смог получить доступ к токену: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Ошибка получения токена: {e}")
    return None

def is_question_time(current_time):
    """Check if current time is a valid question time (every 30 minutes from 9:00 to 17:00)"""
    start_time = time(9, 0)
    end_time   = time(17, 0)
    return start_time <= current_time <= end_time and current_time.minute in (0, 30)

def send_message_via_http(user, message_text, access_token):
    """Send message via HTTP request"""
    try:
        if not user.conversation_reference:
            logger.warning(f"Нет ссылки на чат для пользователя {user.name}")
            return False
        conv_ref = json.loads(user.conversation_reference)
        activity = {
            "type": "message",
            "text": message_text,
            "from": conv_ref["bot"],
            "recipient": conv_ref["user"],
            "conversation": conv_ref["conversation"],
            "channelId": conv_ref["channelId"],
            "serviceUrl": conv_ref["serviceUrl"]
        }
        url = (
            f"{conv_ref['serviceUrl']}"
            f"/v3/conversations/{conv_ref['conversation']['id']}/activities"
        )
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type':  'application/json'
        }
        resp = requests.post(url, headers=headers, json=activity, timeout=10)
        if resp.status_code in (200, 201):
            return True
        logger.error(f"HTTP send failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Ошибка отправки через HTTP: {e}")
    return False

# ——— Настройка OpenAI ———
openai.api_key = settings.OPENAI_API_KEY

def get_openai_summary(responses):
    """
    Формируем prompt из списка UserResponse и запрашиваем у ChatGPT
    краткое обобщение активности за день.
    """
    lines = []
    for r in responses:
        ts = r.question_time.strftime('%H:%M')
        txt = r.response_text or "Нет ответа"
        lines.append(f"{ts} — {txt}")
    prompt = (
        "Ты — ассистент, задача которого кратко и ясно обобщить активность пользователя за день.\n"
        "Сформируй один абзац, где перечислишь основные моменты.\n\n"
        "Данные:\n" + "\n".join(lines)
    )
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты — эксперт по аннотированию пользовательской активности."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=400,
        temperature=0.5,
    )

    return resp.choices[0].message.content.strip()

@shared_task
def send_activity_questions():
    """Send activity questions to all active users at 30-minute intervals"""
    try:
        now     = get_kazakhstan_time()
        current = now.time()
        today   = now.date()
        logger.info(f"Activity check at {now.strftime('%H:%M')}")
        if not is_question_time(current):
            return

        users = TeamsUser.objects.filter(is_active=True)
        if not users.exists():
            logger.warning("No active users")
            return

        token = get_access_token()
        if not token:
            return

        text = "Что вы делаете сейчас?"
        for u in users:
            try:
                UserResponse.objects.get_or_create(
                    user=u,
                    question_time=current,
                    question_date=today,
                    defaults={'response_text': ''}
                )
                send_message_via_http(u, text, token)
            except Exception as e:
                logger.error(f"Error sending question to {u.name}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в send_activity_questions: {e}")

@shared_task
def send_message_to_user(user_id: str, message_text: str):
    """Send a message to a specific user"""
    try:
        user = TeamsUser.objects.filter(user_id=user_id, is_active=True).first()
        if not user or not user.conversation_reference:
            return
        token = get_access_token()
        if token:
            send_message_via_http(user, message_text, token)
    except Exception as e:
        logger.error(f"Ошибка в send_message_to_user: {e}")

@shared_task
def send_daily_summary():
    """Send AI summary to all active users at 17:00"""
    try:
        now     = get_kazakhstan_time()
        today = now.date()
        current = now.time()
        logger.info(f"AI summary check at {now.strftime('%H:%M')}")
        if current.hour != 17 and current.minute != 0:
            return

        users = TeamsUser.objects.filter(is_active=True)
        if not users.exists():
            logger.warning("No active users")
            return

        token = get_access_token()
        if not token:
            return

        for u in users:
            try:
                qs = u.responses.filter(question_date = today).order_by('question_time')
                if not qs.exists():
                    continue
                ai_text = get_openai_summary(qs)
                msg = f"📊 **Ежедневный отчёт для {u.name}**\n\n{ai_text}"
                send_message_via_http(u, msg, token)
            except Exception as e:
                logger.error(f"Error sending AI summary to {u.name}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в send_ai_summary: {e}")


@shared_task
def cleanup_old_responses():
    """Task to clean up old responses (older than 30 days)"""
    try:
        cutoff = get_kazakhstan_time().date() - timedelta(days=30)
        deleted_count = UserResponse.objects.filter(question_date__lt=cutoff).delete()[0]
        logger.info(f"Deleted {deleted_count} old responses")
        return deleted_count
    except Exception as e:
        logger.error(f"Ошибка удаления старых ответов: {e}")
        return 0

@shared_task
def health_check():
    """Health check task to verify bot is working"""
    try:
        now = get_kazakhstan_time()
        active = TeamsUser.objects.filter(is_active=True).count()
        token_ok = bool(get_access_token())
        logger.info(f"Health: {now.strftime('%Y-%m-%d %H:%M')}, Users: {active}, Token OK: {token_ok}")
        return {'timestamp': now.isoformat(), 'active_users': active, 'token': token_ok}
    except Exception as e:
        logger.error(f"Ошибка в health_check: {e}")
        return None
