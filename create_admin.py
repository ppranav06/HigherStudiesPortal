import os
import django
import sys
from dotenv import load_dotenv

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from higherstudiesportal.models import Faculty
from higherstudiesportal.utils.supabase_auth import register_user

def create_admin():
    print("Create Admin Account")
    print("-" * 50)
    
    email = input("Enter admin email: ")
    password = input("Enter password: ")
    full_name = input("Enter full name: ")
    department = input("Enter department: ")
    
    # Load environment variables
    load_dotenv()
    
    # Check if email is in allowed admin list
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    if email not in admin_emails:
        print("Error: This email is not in the allowed admin emails list")
        print("Please add it to ADMIN_EMAILS in your .env file first")
        return
    
    try:
        # Register the admin user
        result = register_user(
            email=email,
            password=password,
            full_name=full_name,
            department=department,
            designation="Admin",
            graduation_year=None
        )
        
        if result['success']:
            print(f"\nAdmin account created successfully for {email}")
            print("You can now log in using these credentials")
        else:
            print(f"\nError creating admin account: {result['error']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_admin() 