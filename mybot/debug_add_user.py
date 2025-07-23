#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot1.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from bot2.models import TeamsUser
from django.utils import timezone
from django.db import connection

def check_database_connection():
    """Check if database connection is working"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_table_exists():
    """Check if teams_users table exists"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'teams_users'
                );
            """)
            result = cursor.fetchone()
            exists = result[0]
            print(f"✅ Teams users table exists: {exists}")
            return exists
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return False

def count_existing_users():
    """Count existing users in the table"""
    try:
        count = TeamsUser.objects.count()
        print(f"✅ Current user count: {count}")
        return count
    except Exception as e:
        print(f"❌ Error counting users: {e}")
        return -1

def add_user(user_id, name="Test User", email=None, tenant_id="test-tenant", conversation_id="test-conversation"):
    """Add a user to the database"""
    try:
        print(f"\n🔍 Attempting to add user: {user_id}")
        
        # Check if user already exists
        existing_user = TeamsUser.objects.filter(user_id=user_id).first()
        if existing_user:
            print(f"⚠️  User with ID {user_id} already exists: {existing_user}")
            return existing_user

        # Create new user
        user = TeamsUser.objects.create(
            user_id=user_id,
            name=name,
            email=email,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            is_active=True
        )

        print(f"✅ Successfully created user: {user}")
        
        # Verify the user was saved
        saved_user = TeamsUser.objects.get(user_id=user_id)
        print(f"✅ Verified user in database: {saved_user}")
        
        return user

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    print("🔧 Database Debug Script")
    print("=" * 50)
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Check if table exists
    if not check_table_exists():
        print("❌ Teams users table does not exist")
        sys.exit(1)
    
    # Count existing users
    count_existing_users()
    
    # Add the specific user
    user_id = "7612d2d1-1157-4143-ac5b-246adf627dac"
    
    print(f"\n👤 Adding user with ID: {user_id}")
    user = add_user(
        user_id=user_id,
        name="Test User",
        email=None,
        tenant_id="test-tenant",
        conversation_id="test-conversation"
    )
    
    if user:
        print(f"\n📋 User details:")
        print(f"  ID: {user.user_id}")
        print(f"  Name: {user.name}")
        print(f"  Created: {user.created_at}")
        print(f"  Active: {user.is_active}")
        
        # Final count
        final_count = TeamsUser.objects.count()
        print(f"\n📊 Final user count: {final_count}")
    else:
        print("❌ Failed to add user") 