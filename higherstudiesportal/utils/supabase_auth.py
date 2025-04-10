"""
Supabase Auth

Custom authentication backend with supabase
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase.client import create_client
from dotenv import load_dotenv
import os

# getURLKEY = lambda: (os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

class SupabaseAuthBackend(BaseBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):
        load_dotenv('.env')
        URL, KEY = os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')
        supabase = create_client(supabase_url=URL, supabase_key=KEY)
        try:
            response = supabase.auth.sign_in_with_password(
                {
                    'email': username,
                    'password': password
                }
            )
            user_data = response.user
            user = User.objects.get(username=user_data.email)
            return user
        except User.DoesNotExist as e:
            print(f"Error: User does not exist: {e}")
        except Exception as e:
            print(f"Authentication error: {e}")

    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None