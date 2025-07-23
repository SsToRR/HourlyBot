#!/usr/bin/env python3
"""
Simple script to send hourly question - no async issues
Usage: python simple_question.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot1.settings')
django.setup()

from bot2.models import TeamsUser, UserResponse
from datetime import datetime

def send_hourly_question():
    """Send hourly question to all active users"""
    print("🤖 Simple Hourly Question Sender")
    print("=" * 40)
    
    # Get current time
    current_time = datetime.now().time()
    current_date = datetime.now().date()
    
    # Get all active users
    active_users = TeamsUser.objects.filter(is_active=True)
    
    if not active_users.exists():
        print("❌ No active users found!")
        print("Make sure you've sent 'start' to the bot in Teams first.")
        return
    
    question_text = "What are you doing right now? 📝"
    
    print(f"📋 Found {active_users.count()} active user(s)")
    print(f"⏰ Current time: {current_time.strftime('%H:%M')}")
    print(f"📅 Current date: {current_date}")
    print(f"❓ Question: {question_text}")
    print("-" * 40)
    
    for user in active_users:
        print(f"\n👤 Processing user: {user.name}")
        
        # Create a placeholder response record
        response, created = UserResponse.objects.get_or_create(
            user=user,
            question_time=current_time,
            question_date=current_date,
            defaults={'response_text': ''}
        )
        
        if created:
            print(f"  ✅ Created question record")
        else:
            print(f"  ℹ️  Question record already exists")
        
        # Check if user has conversation reference
        if user.conversation_reference:
            print(f"  ✅ Has conversation reference")
            print(f"  📤 Would send: {question_text}")
            print(f"  💡 To actually send the message, use the trigger_question.py script")
        else:
            print(f"  ❌ No conversation reference found")
    
    print("\n" + "=" * 40)
    print("📊 Summary: Question records created successfully!")
    print("💡 To send actual messages, run: python trigger_question.py")

if __name__ == "__main__":
    send_hourly_question() 