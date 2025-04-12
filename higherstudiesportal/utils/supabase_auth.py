"""
Supabase Auth

Custom authentication backend with supabase
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase.client import create_client
from dotenv import load_dotenv
from higherstudiesportal.models import Student, Faculty
from .re_patterns_email import student_pattern,faculty_pattern

import os
import re

getURLKEY = lambda: (os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

class SupabaseAuthBackend(BaseBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):
        load_dotenv('.env')
        URL, KEY = getURLKEY()
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

def determine_role_from_email(email):
    """Determine if the email belongs to a student or faculty"""
    if re.match(student_pattern, email):
        return 'student'
    elif re.match(faculty_pattern, email):
        return 'faculty'
    else:
        return 'unknown'

def register_user(email, password, full_name, department=None, graduation_year=None, designation=None):
    """Register a new user with Supabase and create corresponding Django user"""
    URL, KEY = getURLKEY()
    supabase = create_client(supabase_url=URL, supabase_key=KEY)
    
    # Determine role from email
    role = determine_role_from_email(email)
    
    # Sign up with Supabase
    try:
        signup_data = {
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "user_role": role,
                    "full_name": full_name
                }
            }
        }
        
        response = supabase.auth.sign_up(signup_data)
        user_data = response.user
        
        # Create profile based on role
        if role == 'student':
            profile_data = {
                "id": user_data.id,
                "email": email,
                "full_name": full_name,
                "department": department,
                "graduation_year": graduation_year
            }
            supabase.table('student').insert(profile_data).execute()
            # Create user in model
            Student.objects.create(
                user = user_data,
                department = profile_data['department'],
                graduation_year = profile_data['graduation_year'],
            )
            
        elif role == 'faculty':
            profile_data = {
                "id": user_data.id, 
                "email": email,
                "full_name": full_name,
                "department": department,
                "designation": designation
            }
            supabase.table('faculty').insert(profile_data).execute()
            # Create user in model
            Faculty.objects.create(
                user = user_data,
                department = profile_data['department'],
                designation = profile_data['designation'],
            )
        
        # Create Django user
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password  # Django will hash this
        )
        
        return {
            "success": True,
            "user": django_user,
            "role": role
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }