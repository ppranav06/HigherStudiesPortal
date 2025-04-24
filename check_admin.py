import os
import django
from dotenv import load_dotenv

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from higherstudiesportal.models import SupabaseUser
from higherstudiesportal.utils.supabase_auth import get_supabase_client

def check_and_fix_admin():
    load_dotenv()
    email = "poornima2310587@ssn.edu.in"
    
    # Check Django user
    try:
        user = User.objects.get(email=email)
        print(f"\nDjango user exists:")
        print(f"Username: {user.username}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        
        # Make sure user has admin privileges
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print("Updated user with admin privileges")
            
    except User.DoesNotExist:
        print(f"\nNo Django user found with email {email}")
        return
    
    # Check Supabase link
    try:
        supabase_user = SupabaseUser.objects.get(user=user)
        print(f"Supabase link exists with UUID: {supabase_user.supabase_uuid}")
    except SupabaseUser.DoesNotExist:
        print("No Supabase link found")
        
        # Try to get Supabase user info
        supabase = get_supabase_client()
        try:
            response = supabase.auth.admin.users.list()
            users = response.users
            for supabase_user in users:
                if supabase_user.email == email:
                    print(f"Found Supabase user with UUID: {supabase_user.id}")
                    # Create the link
                    SupabaseUser.objects.create(
                        user=user,
                        supabase_uuid=supabase_user.id
                    )
                    print("Created Supabase link")
                    break
        except Exception as e:
            print(f"Error checking Supabase: {str(e)}")

if __name__ == "__main__":
    check_and_fix_admin() 