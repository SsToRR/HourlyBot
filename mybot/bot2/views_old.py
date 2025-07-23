import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity
from .bot_handler import TeamsBot

logger = logging.getLogger(__name__)

# Create adapter with optional authentication for emulator testing
def get_adapter():
    """Get bot adapter with or without authentication based on environment"""
    # Check if we're in emulator mode (no app password provided)
    app_id = getattr(settings, 'BOT_FRAMEWORK_APP_ID', None)
    app_password = getattr(settings, 'BOT_FRAMEWORK_APP_PASSWORD', None)
    
    if app_id and app_password:
        # Production mode with authentication
        settings_obj = BotFrameworkAdapterSettings(
            app_id=app_id,
            app_password=app_password
        )
    else:
        # Emulator mode without authentication - use empty strings
        settings_obj = BotFrameworkAdapterSettings(
            app_id="", 
            app_password=""
        )
    
    adapter = BotFrameworkAdapter(settings_obj)
    
    # For emulator mode, disable authentication
    if not app_password:
        # Override the authenticate_request method to skip authentication
        async def no_auth_authenticate_request(request, auth_header):
            # Skip authentication for emulator
            logger.info("Skipping authentication for emulator mode")
            # Return a mock identity for emulator
            from botframework.connector.auth import ClaimsIdentity
            return ClaimsIdentity(claims={}, is_authenticated=True)
        
        adapter._authenticate_request = no_auth_authenticate_request
    
    # Add error handler for emulator mode
    async def on_turn_error(turn_context, exception):
        logger.error(f"Exception caught: {exception}")
        # Don't try to send error messages in emulator mode
        # This prevents ConnectorClient errors
    
    adapter.on_turn_error = on_turn_error
    
    return adapter

# Create bot instance
BOT = TeamsBot()

@csrf_exempt
@require_http_methods(["POST"])
def messages(request):
    if request.method == "POST":
        try:
            body = request.body.decode('utf-8')
            logger.info(f"Received request body: {body[:200]}...")
            
            # Basic validation
            if not body.strip():
                logger.error("Empty request body")
                return JsonResponse({"error": "Empty request body"}, status=400)
            
            try:
                body_dict = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body: {e}")
                return JsonResponse({"error": "Invalid JSON"}, status=400)
            
            # Check if required fields exist
            if 'type' not in body_dict:
                logger.error("Missing 'type' field in activity")
                return JsonResponse({"error": "Missing 'type' field"}, status=400)
            
            try:
                activity = Activity().deserialize(body_dict)
                logger.info(f"Deserialized activity type: {activity.type}")
            except Exception as e:
                logger.error(f"Error deserializing activity: {e}")
                return JsonResponse({"error": "Invalid activity format"}, status=400)
            
            # Get adapter
            try:
                adapter = get_adapter()
            except Exception as e:
                logger.error(f"Error creating adapter: {e}")
                return JsonResponse({"error": "Bot adapter error"}, status=500)
            
            # Process the activity
            async def process_activity():
                try:
                    # Use the service URL from the activity if available, otherwise use ngrok URL
                    service_url = getattr(activity, 'service_url', None) or getattr(settings, 'NGROK_URL', 'https://c7f90181e475.ngrok-free.app')
                    logger.info(f"Processing activity with service URL: {service_url}")
                    
                    # Set the service URL on the activity for the adapter to use
                    activity.service_url = service_url
                    
                    # For emulator mode, we'll use a simpler approach
                    if activity.channel_id in ['emulator', 'webchat']:
                        # Create a turn context and process the activity directly
                        turn_context = TurnContext(adapter, activity)
                        
                        # Call the bot's on_turn method directly
                        await BOT.on_turn(turn_context)
                        
                        # Check if the bot generated a response
                        if hasattr(turn_context, '_emulator_response'):
                            # Return the bot's response to the emulator
                            logger.info(f"✅ Returning emulator response: {turn_context._emulator_response.get('text', 'No text')}")
                            
                            # Debug: Log the full response structure
                            import json
                            try:
                                # Test if it's serializable
                                json.dumps(turn_context._emulator_response)
                                logger.info("✅ Response is JSON serializable")
                                return JsonResponse(turn_context._emulator_response)
                            except TypeError as e:
                                logger.error(f"❌ JSON serialization failed: {e}")
                                # Fallback: return a simple response
                                return JsonResponse({
                                    "type": "message",
                                    "text": turn_context._emulator_response.get('text', 'Bot response'),
                                    "from": {
                                        "id": "bot-id",
                                        "name": "Bot",
                                        "role": "bot"
                                    },
                                    "conversation": {
                                        "id": "conversation-id"
                                    },
                                    "recipient": {
                                        "id": "user-id",
                                        "name": "User",
                                        "role": "user"
                                    },
                                    "channelId": "emulator",
                                    "serviceUrl": "https://c7f90181e475.ngrok-free.app"
                                })
                        else:
                            # Return a simple success response
                            logger.info("❌ No emulator response found in turn context")
                            return JsonResponse({
                                "status": "success",
                                "message": "Activity processed successfully"
                            })
                    else:
                        # For non-emulator, use the adapter's process_activity method
                        await adapter.process_activity(activity, service_url, BOT.on_turn)
                        
                        logger.info("Successfully processed activity")
                        
                except Exception as e:
                    logger.error(f"Error in process_activity: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise
            
            # Run the async function
            try:
                import asyncio
                asyncio.run(process_activity())
            except Exception as e:
                logger.error(f"Error running async process: {e}")
                return JsonResponse({"error": f"Processing error: {str(e)}"}, status=500)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    
    return HttpResponse(status=405)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({"status": "healthy", "service": "Teams Bot"})

@csrf_exempt
@require_http_methods(["POST"])
def test_message(request):
    """Test endpoint for debugging"""
    try:
        body = request.body.decode('utf-8')
        return JsonResponse({
            "status": "received",
            "body_length": len(body),
            "body_preview": body[:200],
            "headers": dict(request.headers)
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def proactive_message(request):
    """Endpoint for sending proactive messages to users"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        message_text = data.get('message', 'What are you doing right now?')
        
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=400)
        
        # In a real implementation, you would send the message here
        # For now, we'll just log it
        logger.info(f"Would send proactive message to {user_id}: {message_text}")
        
        return JsonResponse({"status": "message queued", "user_id": user_id})
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error sending proactive message: {e}")
        return JsonResponse({"error": str(e)}, status=500)
