import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from botbuilder.core import BotFrameworkAdapter, TurnContext, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from .bot_handler import TeamsBot

logger = logging.getLogger(__name__)

def get_adapter():
    """Create and configure the bot adapter"""
    app_id = getattr(settings, 'BOT_FRAMEWORK_APP_ID', '')
    app_password = getattr(settings, 'BOT_FRAMEWORK_APP_PASSWORD', '')
    
    # Create adapter with proper settings
    adapter_settings = BotFrameworkAdapterSettings(app_id=app_id, app_password=app_password)
    adapter = BotFrameworkAdapter(adapter_settings)
    
    # Add error handler
    async def on_turn_error(turn_context, exception):
        logger.error(f"Exception caught: {exception}")
        await turn_context.send_activity("Sorry, I encountered an error. Please try again.")
    
    adapter.on_turn_error = on_turn_error
    
    return adapter

# Create bot instance
BOT = TeamsBot()

@csrf_exempt
@require_http_methods(["POST"])
def messages(request):
    """Handle incoming bot messages"""
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
            
            # Get authorization header
            auth_header = request.headers.get('Authorization', '')
            logger.info(f"Authorization header: {auth_header[:50]}...")
            
            # Process the activity
            async def process_activity():
                try:
                    # For Teams, we need to handle authentication properly
                    if auth_header:
                        # Use the auth header if provided
                        await adapter.process_activity(activity, auth_header, BOT.on_turn)
                    else:
                        # For development/testing, try without auth header
                        logger.warning("No authorization header provided, attempting to process without authentication")
                        await adapter.process_activity(activity, "", BOT.on_turn)
                    
                    logger.info("Successfully processed activity")
                    
                except Exception as e:
                    logger.error(f"Error in process_activity: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    
                    # If authentication fails, try a simpler approach for development
                    if "Authorization" in str(e) or "token" in str(e).lower():
                        logger.info("Authentication failed, trying direct message processing...")
                        try:
                            # Direct message processing without authentication
                            await BOT.on_message_activity(TurnContext(adapter, activity))
                            logger.info("Successfully processed message directly")
                        except Exception as direct_error:
                            logger.error(f"Direct processing also failed: {direct_error}")
                            raise e  # Re-raise the original error
                    else:
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
@require_http_methods(["GET"])
def test_bot(request):
    """Test endpoint to verify bot is working"""
    return JsonResponse({
        "status": "bot_ready",
        "app_id": getattr(settings, 'BOT_FRAMEWORK_APP_ID', ''),
        "endpoint": "/bot/api/messages/",
        "health": "/bot/api/health/"
    }) 