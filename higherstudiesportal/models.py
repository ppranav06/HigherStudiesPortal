from django.db import models
from django.contrib.auth.backends import BaseBackend
from supabase.client import create_client, Client
from dotenv import load_dotenv
import os

class SupabaseClient():
    def __init__(self):
        load_dotenv()
        URL=os.environ.get('SUPABASE_URL')
        KEY=os.environ.get('SUPABASE_KEY')
        self.client = create_client(supabase_url=URL, supabase_key=KEY) # supabase client type

    def sign_up(self, email, password):
        user = self.client.auth.sign_up(
            {
                'email': email,
                'password': password
            }
        )
        return user
    
    def sign_in(self, email, password):
        user = self.client.sign_in_with_password(
            {
                'email': email, 
                'password': password
            }
        )
        return user
    
class SupabaseAuthBackend(BaseBackend):
    def authenticate(self, request, username = ..., password = ..., **kwargs):
        URL, KEY = os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')
        supabase = create_client(supabase_url=URL, supabase_key=KEY)

    
    def get_user(self, user_id):
        try:
            return 