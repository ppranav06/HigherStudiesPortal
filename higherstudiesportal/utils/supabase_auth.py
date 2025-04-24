"""
Supabase Auth

Custom authentication backend with supabase
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase.client import create_client
from dotenv import load_dotenv
from higherstudiesportal.models import Student, Faculty, SupabaseUser
from .re_patterns_email import student_pattern, faculty_pattern, admin_pattern

import os
import re

getURLKEY = lambda: (os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

def get_supabase_client():
    """Creates the client and returns the client object"""
    load_dotenv('.env')
    URL, KEY = getURLKEY()
    # print(f"Debug - Supabase URL: {URL}")
    # print(f"Debug - Supabase Key exists: {bool(KEY)}")
    supabase = create_client(supabase_url=URL, supabase_key=KEY)
    return supabase

class SupabaseAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        supabase = get_supabase_client()
        try:
            response = supabase.auth.sign_in_with_password(
                {
                    'email': username,
                    'password': password
                }
            )
            user_data = response.user
            supabase_uuid = user_data.id
            
            # Try to find user by Supabase UUID
            try:
                supabase_user = SupabaseUser.objects.get(supabase_uuid=supabase_uuid)
                return supabase_user.user
            except SupabaseUser.DoesNotExist:
                # If no link exists, try to find by email
                try:
                    django_user = User.objects.get(email=username)
                    # Create the link
                    SupabaseUser.objects.create(
                        user=django_user,
                        supabase_uuid=supabase_uuid
                    )
                    return django_user
                except User.DoesNotExist:
                    # Create new user
                    django_user = User.objects.create_user(
                        username=username,
                        email=username,
                        password=password  # Django will hash this
                    )
                    SupabaseUser.objects.create(
                        user=django_user,
                        supabase_uuid=supabase_uuid
                    )
                    return django_user
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

def determine_role_from_email(email):
    """Determine if the email belongs to a student, faculty, or admin"""
    # Load environment variables
    load_dotenv()
    
    # First check if email is in ADMIN_EMAILS
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    admin_emails = [e.strip() for e in admin_emails if e.strip()]  # Clean the email list
    
    # print(f"Debug - Email being checked: {email}")
    # print(f"Debug - Admin emails from env: {admin_emails}")
    # print(f"Debug - Matches student pattern: {bool(re.match(student_pattern, email))}")
    # print(f"Debug - Matches faculty pattern: {bool(re.match(faculty_pattern, email))}")
    # print(f"Debug - Is in admin emails: {email in admin_emails}")
    
    if email in admin_emails:
        return 'admin'
    elif re.match(student_pattern, email):
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
    
    if role == 'unknown':
        return {
            "success": False,
            "error": "Invalid email format"
        }
    
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
        supabase_uuid = user_data.id
        
        # Create Django user
        first_name = full_name.split()[0] if ' ' in full_name else full_name
        last_name = ' '.join(full_name.split()[1:]) if ' ' in full_name else ''
        
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create the Supabase link
        SupabaseUser.objects.create(
            user=django_user,
            supabase_uuid=supabase_uuid
        )
        
        # Create profile based on role
        if role == 'student':
            # Insert into Supabase
            profile_data = {
                "id": supabase_uuid,
                "email": email,
                "full_name": full_name,
                "department": department,
                "graduation_year": graduation_year
            }
            supabase.table('student').insert(profile_data).execute()
            
            # Create Django model
            Student.objects.create(
                user=django_user,
                department=department,
                graduation_year=graduation_year
            )
            
        elif role == 'faculty':
            # Insert into Supabase
            profile_data = {
                "id": supabase_uuid, 
                "email": email,
                "full_name": full_name,
                "department": department,
                "designation": designation
            }
            supabase.table('faculty').insert(profile_data).execute()
            
            # Create Django model
            Faculty.objects.create(
                user=django_user,
                department=department,
                designation=designation
            )
        
        elif role == 'admin':
            # For admin, we only need the basic user account
            # No additional profile needed
            django_user.is_staff = True
            django_user.is_superuser = True
            django_user.save()
            
            # Insert into Supabase admin table if needed
            profile_data = {
                "id": supabase_uuid,
                "email": email,
                "full_name": full_name,
                "department": department
            }
            supabase.table('admin').insert(profile_data).execute()
        
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
    
def get_supabase_uuid(django_user):
    """Get the Supabase UUID for a Django user"""
    if django_user is None:
        raise ValueError("Cannot get Supabase UUID for None user")
    
    try:
        # Make sure we're querying with a User object
        return SupabaseUser.objects.get(user=django_user).supabase_uuid
    except SupabaseUser.DoesNotExist:
        # Handle the case where the user doesn't have a Supabase record
        raise ValueError(f"No Supabase user found for Django user {django_user.username}")