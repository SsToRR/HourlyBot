import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

from .models import TeamsUser, UserResponse

logger = logging.getLogger(__name__)

class TeamsBot(ActivityHandler):
    """Teams bot handler for hourly check functionality"""
    
    def __init__(self):
        super().__init__()
        self.conversation_references = {}
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages from users"""
        try:
            logger.info(f"Processing message activity: {turn_context.activity.text}")
            
            # Get user information
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            # For emulator, use a default tenant_id since it might not be available
            tenant_id = getattr(turn_context.activity.conversation, 'tenant_id', None) or 'emulator-tenant'
            conversation_id = turn_context.activity.conversation.id
            
            logger.info(f"User: {user_name} ({user_id}) in conversation: {conversation_id}")
            
            # Save or update user in database
            user, created = await sync_to_async(TeamsUser.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'name': user_name or 'Unknown User',
                    'tenant_id': tenant_id,
                    'conversation_id': conversation_id,
                }
            )
            
            if not created:
                # Update existing user's information
                user.name = user_name or user.name
                user.conversation_id = conversation_id
                await sync_to_async(user.save)()
            
            # Store conversation reference for proactive messaging
            self.conversation_references[user_id] = turn_context.activity.get_conversation_reference()
            
            # Check if this is a response to our question
            user_text = turn_context.activity.text.strip()
            
            # Look for the most recent unanswered question for this user
            recent_question = await sync_to_async(
                lambda: UserResponse.objects.filter(
                    user=user,
                    was_answered=False
                ).order_by('-question_asked_at').first()
            )()
            
            if recent_question and user_text:
                # Save the user's response
                recent_question.response_text = user_text
                recent_question.was_answered = True
                await sync_to_async(recent_question.save)()
                
                # Send confirmation
                confirmation_text = "Thank you for your response! I've recorded what you're working on."
                
                # For emulator mode, just log the response
                if turn_context.activity.channel_id in ['emulator', 'webchat']:
                    logger.info(f"EMULATOR RESPONSE: {confirmation_text}")
                    logger.info("Confirmation logged for emulator (not sent via adapter)")
                    
                    # Store the response in turn context for the view to return
                    turn_context._emulator_response = {
                        "type": "message",
                        "text": confirmation_text,
                        "from": {
                            "id": getattr(turn_context.activity.recipient, 'id', None),
                            "name": getattr(turn_context.activity.recipient, 'name', None),
                            "role": "bot"
                        },
                        "conversation": {
                            "id": getattr(turn_context.activity.conversation, 'id', None),
                            "name": getattr(turn_context.activity.conversation, 'name', None),
                            "isGroup": getattr(turn_context.activity.conversation, 'is_group', None),
                            "conversationType": getattr(turn_context.activity.conversation, 'conversation_type', None),
                            "tenantId": getattr(turn_context.activity.conversation, 'tenant_id', None),
                        },
                        "recipient": {
                            "id": getattr(turn_context.activity.from_property, 'id', None),
                            "name": getattr(turn_context.activity.from_property, 'name', None),
                            "role": getattr(turn_context.activity.from_property, 'role', None),
                        },
                        "channelId": turn_context.activity.channel_id,
                        "serviceUrl": turn_context.activity.service_url,
                        "timestamp": str(turn_context.activity.timestamp) if turn_context.activity.timestamp else None
                    }
                else:
                    # For non-emulator, use normal sending
                    reply = MessageFactory.text(confirmation_text)
                    logger.info("Sending confirmation message to user")
                    await turn_context.send_activity(reply)
                    logger.info("Confirmation message sent successfully")
            else:
                # Send welcome message or help
                welcome_text = (
                    "Hello! I'm your hourly check bot. I'll ask you every day at 11:30 AM "
                    "what you're working on to help track your productivity. "
                    "Just respond to my questions when they come up!"
                )
                
                # For emulator mode, just log the response
                if turn_context.activity.channel_id in ['emulator', 'webchat']:
                    logger.info(f"EMULATOR RESPONSE: {welcome_text}")
                    logger.info("Response logged for emulator (not sent via adapter)")
                    
                    # Store the response in turn context for the view to return
                    turn_context._emulator_response = {
                        "type": "message",
                        "text": welcome_text,
                        "from": {
                            "id": getattr(turn_context.activity.recipient, 'id', None),
                            "name": getattr(turn_context.activity.recipient, 'name', None),
                            "role": "bot"
                        },
                        "conversation": {
                            "id": getattr(turn_context.activity.conversation, 'id', None),
                            "name": getattr(turn_context.activity.conversation, 'name', None),
                            "isGroup": getattr(turn_context.activity.conversation, 'is_group', None),
                            "conversationType": getattr(turn_context.activity.conversation, 'conversation_type', None),
                            "tenantId": getattr(turn_context.activity.conversation, 'tenant_id', None),
                        },
                        "recipient": {
                            "id": getattr(turn_context.activity.from_property, 'id', None),
                            "name": getattr(turn_context.activity.from_property, 'name', None),
                            "role": getattr(turn_context.activity.from_property, 'role', None),
                        },
                        "channelId": turn_context.activity.channel_id,
                        "serviceUrl": turn_context.activity.service_url,
                        "timestamp": str(turn_context.activity.timestamp) if turn_context.activity.timestamp else None
                    }
                    logger.info(f"✅ Stored emulator response in turn context: {welcome_text}")
                else:
                    # For non-emulator, use normal sending
                    reply = MessageFactory.text(welcome_text)
                    logger.info("Sending welcome message to user")
                    await turn_context.send_activity(reply)
                    logger.info("Welcome message sent successfully")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Try to send an error message to the user
            try:
                error_text = "Sorry, I encountered an error processing your message. Please try again."
                
                # For emulator mode, just log the error response
                if turn_context.activity.channel_id in ['emulator', 'webchat']:
                    logger.info(f"EMULATOR ERROR RESPONSE: {error_text}")
                    logger.info("Error message logged for emulator (not sent via adapter)")
                else:
                    # For non-emulator, use normal sending
                    error_reply = MessageFactory.text(error_text)
                    await turn_context.send_activity(error_reply)
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
    
    async def on_members_added_activity(self, members_added: list[ChannelAccount], turn_context: TurnContext):
        """Handle when users are added to the conversation"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_text = (
                    "Welcome! I'm your hourly check bot. I'll ask you every day at 11:30 AM "
                    "what you're working on to help track your productivity. "
                    "Just respond to my questions when they come up!"
                )
                
                # For emulator mode, just log the response
                if turn_context.activity.channel_id in ['emulator', 'webchat']:
                    logger.info(f"EMULATOR RESPONSE: {welcome_text}")
                    logger.info("Welcome message logged for emulator (not sent via adapter)")
                    
                    # Store the response in turn context for the view to return
                    turn_context._emulator_response = {
                        "type": "message",
                        "text": welcome_text,
                        "from": {
                            "id": getattr(turn_context.activity.recipient, 'id', None),
                            "name": getattr(turn_context.activity.recipient, 'name', None),
                            "role": "bot"
                        },
                        "conversation": {
                            "id": getattr(turn_context.activity.conversation, 'id', None),
                            "name": getattr(turn_context.activity.conversation, 'name', None),
                            "isGroup": getattr(turn_context.activity.conversation, 'is_group', None),
                            "conversationType": getattr(turn_context.activity.conversation, 'conversation_type', None),
                            "tenantId": getattr(turn_context.activity.conversation, 'tenant_id', None),
                        },
                        "recipient": {
                            "id": getattr(turn_context.activity.from_property, 'id', None),
                            "name": getattr(turn_context.activity.from_property, 'name', None),
                            "role": getattr(turn_context.activity.from_property, 'role', None),
                        },
                        "channelId": turn_context.activity.channel_id,
                        "serviceUrl": turn_context.activity.service_url,
                        "timestamp": str(turn_context.activity.timestamp) if turn_context.activity.timestamp else None
                    }
                else:
                    # For non-emulator, use normal sending
                    reply = MessageFactory.text(welcome_text)
                    await turn_context.send_activity(reply)
    
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle conversation updates"""
        # Store conversation reference for proactive messaging (works for both Teams and emulator)
        if turn_context.activity.from_property:
            user_id = turn_context.activity.from_property.id
            self.conversation_references[user_id] = turn_context.activity.get_conversation_reference()
            logger.info(f"Stored conversation reference for user: {user_id}")
        
        await super().on_conversation_update_activity(turn_context)
    
    async def ask_question_to_user(self, user_id: str) -> bool:
        """Ask the hourly question to a specific user"""
        try:
            conversation_ref = self.conversation_references.get(user_id)
            if not conversation_ref:
                logger.warning(f"No conversation reference found for user {user_id}")
                return False
            
            # Create a new activity
            activity = Activity(
                type=ActivityTypes.message,
                text="What are you doing right now?",
                conversation=conversation_ref.conversation,
                recipient=conversation_ref.bot,
                from_property=conversation_ref.user
            )
            
            # Send the message
            # Note: This would require a bot adapter instance
            # For now, we'll just log that we would send the message
            logger.info(f"Would send question to user {user_id}: 'What are you doing right now?'")
            
            # Create a record of the question being asked
            try:
                user = await sync_to_async(TeamsUser.objects.get)(user_id=user_id)
                await sync_to_async(UserResponse.objects.create)(
                    user=user,
                    question_asked_at=timezone.now(),
                    response_text="",
                    was_answered=False
                )
                return True
            except TeamsUser.DoesNotExist:
                logger.error(f"User {user_id} not found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error asking question to user {user_id}: {e}")
            return False 