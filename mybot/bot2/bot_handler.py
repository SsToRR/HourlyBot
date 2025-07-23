import logging
import json
from datetime import datetime, time
from django.utils import timezone
from asgiref.sync import sync_to_async
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount
from .models import TeamsUser, UserResponse
import pytz

logger = logging.getLogger(__name__)

def get_kazakhstan_time():
    """Get current time in Kazakhstan timezone"""
    kazakhstan_tz = pytz.timezone('Asia/Almaty')
    return timezone.now().astimezone(kazakhstan_tz)

class TeamsBot(ActivityHandler):
    """Simple Teams bot for hourly check-ins"""
    
    def __init__(self):
        super().__init__()
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages"""
        try:
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name or "Unknown User"
            message_text = turn_context.activity.text.strip().lower()
            
            # Store conversation reference in database for proactive messaging
            conversation_ref = turn_context.activity.get_conversation_reference()
            conversation_ref_json = json.dumps(conversation_ref.serialize())
            
            # Update or create user with conversation reference
            user, created = await sync_to_async(TeamsUser.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'name': user_name,
                    'conversation_reference': conversation_ref_json
                }
            )
            
            if not created:
                # Update existing user's conversation reference
                user.conversation_reference = conversation_ref_json
                await sync_to_async(user.save)()
            
            logger.info(f"Received message from {user_name} ({user_id}): {message_text}")
            
            if message_text == "start":
                await self._handle_start_command(turn_context, user_id, user_name)
            elif message_text == "stop":
                await self._handle_stop_command(turn_context, user_id)
            else:
                await self._handle_regular_message(turn_context, user_id, message_text)
                
        except Exception as e:
            logger.error(f"Ошибка управление сообщением: {e}")
            await turn_context.send_activity("Извините, я наткнулся на проблему. Пожалуйста, попробуйте позже.")
    
    async def _handle_start_command(self, turn_context: TurnContext, user_id: str, user_name: str):
        """Handle the 'start' command"""
        try:
            # Get or create user
            user, created = await sync_to_async(TeamsUser.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'name': user_name,
                    'is_active': True
                }
            )
            
            if created:
                await turn_context.send_activity(
                    f"Доброго времени суток, {user_name}! 🎉\n\n"
                    "Я твой ежечасный отчет. Я буду спрашивать вас что вы делаете в:\n"
                    "• 9:00 AM\n"
                    "• 9:30 AM\n"
                    "• 10:00 AM\n"
                    "• 10:30 AM\n"
                    "• 11:00 AM\n"
                    "• 11:30 AM\n"
                    "• 12:00 PM\n"
                    "• 12:30 PM\n"
                    "• 2:00 PM\n"
                    "• 2:30 PM\n"
                    "• 3:00 PM\n"
                    "• 3:30 PM\n"
                    "• 4:00 PM\n"
                    "• 4:30 PM\n"
                    "• 5:00 PM\n\n"
                    "Просто отвечай на мои вопросы когда они появляются! 📝\n\n"
                    "Напишите 'stop' чтобы отписаться от моих вопросов."
                )
                logger.info(f"New user registered: {user_name} ({user_id})")
            else:
                if user.is_active:
                    await turn_context.send_activity(
                        f"Добро пожаловать {user_name}! Вы уже подписаны на мои ежечасные вопросы. 📋\n\n"
                        "Напишите 'stop' чтобы отписаться."
                    )
                else:
                    user.is_active = True
                    await sync_to_async(user.save)()
                    await turn_context.send_activity(
                        f"Добро пожаловать {user_name}! Вы теперь подписаны на мои ежечасные вопросы снова. 📋\n\n"
                        "Напиши 'stop' чтобы отписаться."
                    )
                    logger.info(f"User reactivated: {user_name} ({user_id})")
                    
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await turn_context.send_activity("Извините, я не смог обработать вашу команду. Пожалуйста, попробуйте еще раз.")
    
    async def _handle_stop_command(self, turn_context: TurnContext, user_id: str):
        """Handle the 'stop' command"""
        try:
            user = await sync_to_async(TeamsUser.objects.filter(user_id=user_id).first)()
            
            if user and user.is_active:
                user.is_active = False
                await sync_to_async(user.save)()
                await turn_context.send_activity(
                    f"До свидания {user.name}! 👋\n\n"
                    "Вы отписаны от моих ежечасных вопросов. Я буду скучать :(\n\n"
                    "Напишите 'start' чтобы снова подписаться."
                )
                logger.info(f"User unsubscribed: {user.name} ({user_id})")
            else:
                await turn_context.send_activity(
                    "Вы не подписаны на мои ежечасные вопросы.\n\n"
                    "Напишите 'start' чтобы снова подписаться."
                )
                
        except Exception as e:
            logger.error(f"Error in stop command: {e}")
            await turn_context.send_activity("Извините, я не смог обработать вашу команду. Пожалуйста, попробуйте еще раз.")
    
    async def _handle_regular_message(self, turn_context: TurnContext, user_id: str, message_text: str):
        """Handle regular messages (responses to questions)"""
        try:
            user = await sync_to_async(TeamsUser.objects.filter(user_id=user_id, is_active=True).first)()
            
            if not user:
                await turn_context.send_activity(
                    "Привет! Я не могу распознать вас как подписанного пользователя.\n\n"
                    "Напишите 'start' чтобы подписаться на мои ежечасные вопросы!"
                )
                return
            
            # Check if this is a response to today's question - USE KAZAKHSTAN TIME
            today = get_kazakhstan_time().date()
            current_time = get_kazakhstan_time().time()
            
            # Define question times (in Kazakhstan time)
            question_times = [time(9, 0), time(9, 30), time(10, 0), time(10, 30), 
                            time(10, 45), time(10, 50), time(11, 0), time(11, 30), 
                            time(12, 0), time(12, 30), time(14, 0), time(14, 30), 
                            time(15, 0), time(15, 30), time(16, 0), time(16, 30), 
                            time(17, 0)]
            
            # Find the most recent question time that has passed
            target_question_time = None
            for q_time in sorted(question_times, reverse=True):  # Check from latest to earliest
                if current_time >= q_time:
                    target_question_time = q_time
                    break
            
            if target_question_time:
                # Check if we already have a response for this time today
                existing_response = await sync_to_async(
                    UserResponse.objects.filter(
                        user=user,
                        question_time=target_question_time,
                        question_date=today
                    ).first
                )()
                
                if existing_response:
                    # Update existing response
                    existing_response.response_text = message_text
                    await sync_to_async(existing_response.save)()
                    await turn_context.send_activity(
                        f"✅ Обновил ваш ответ за {target_question_time.strftime('%I:%M %p')}:\n"
                        f"\"{message_text}\"\n\n"
                        "Спасибо за ответ! :)"
                    )
                else:
                    # Create new response
                    await sync_to_async(UserResponse.objects.create)(
                        user=user,
                        question_time=target_question_time,
                        question_date=today,
                        response_text=message_text
                    )
                    await turn_context.send_activity(
                        f"✅ Записал ваш ответ за {target_question_time.strftime('%I:%M %p')}:\n"
                        f"\"{message_text}\"\n\n"
                        "Спасибо за ответ! :) "
                    )
            else:
                await turn_context.send_activity(
                    "Спасибо за ответ! Я буду спрашивать вас о вашей активности в определенные часы.\n\n"
                    "Напишите 'stop' чтобы отписаться от моих вопросов."
                )
                
        except Exception as e:
            logger.error(f"Error handling regular message: {e}")
            await turn_context.send_activity("Извините, я не смог сохранить ваш ответ. Пожалуйста, попробуйте еще раз.")
    
    async def on_members_added_activity(self, members_added: list[ChannelAccount], turn_context: TurnContext):
        """Handle when users are added to the conversation"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "👋 Привет! Я ваш ежечасный отчет.\n\n"
                    "Напишите 'start' чтобы подписаться на мои ежечасные вопросы и начать отслеживать свою работу!\n\n"
                    "Я буду спрашивать вас о вашей активности каждые 30 минут с 9:00 до 17:30."
                )
    
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle conversation updates"""
        if turn_context.activity.from_property:
            user_id = turn_context.activity.from_property.id
            # The conversation_reference is now stored in the TeamsUser model,
            # so we don't need to re-store it here for proactive messaging.
            # However, if the user's conversation_reference changes, we might need to update it.
            # For now, we'll just log the user ID.
            logger.info(f"Stored conversation reference for user: {user_id}")
        
        await super().on_conversation_update_activity(turn_context) 