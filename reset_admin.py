import os
import django
from dotenv import load_dotenv
from supabase.client import create_client

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from higherstudiesportal.models import SupabaseUser

def reset_admin():
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"\nSupabase Configuration:")
    print(f"URL: {url}")
    print(f"Key exists: {bool(key)}")
    
    email = "poornima2310587@ssn.edu.in"
    password = "hello123"
    full_name = "Poornima"
    
    # First, clean up any existing Django user
    try:
        User.objects.filter(email=email).delete()
        print("\nRemoved existing Django user")
    except Exception as e:
        print(f"\nError removing Django user: {str(e)}")
    
    try:
        supabase = create_client(url, key)
        
        print("\nTrying to create Supabase user...")
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "user_role": "admin"
                }
            }
        })
        
        supabase_user = response.user
        print("Supabase user created!")
        print(f"User ID: {supabase_user.id}")
        
        # Create Django user with admin privileges
        print("\nCreating Django user...")
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )
        django_user.is_staff = True
        django_user.is_superuser = True
        django_user.save()
        
        # Create Supabase link
        SupabaseUser.objects.create(
            user=django_user,
            supabase_uuid=supabase_user.id
        )
        
        print("\nAdmin account created successfully!")
        print("You can now log in with:")
        print(f"Email: {email}")
        print(f"Password: {password}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    reset_admin() 