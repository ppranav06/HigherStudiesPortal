from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .utils.supabase_auth import determine_role_from_email, register_user

# @login_required # enforce after auth is set up
def lor_application_student(request):
    return render(request, 'student/lor_application.html')

def lor_tracking_student(request):
    return render(request, 'student/lor_tracking.html')

def dashboard(request):
    """Returns the dashboard depending upon the type of user"""
    if not request.method == "GET":
        return
    
    

def dashboard_student(request):
    return render(request, 'student/student_dashboard.html')

def dashboard_faculty(request):
    return render(request, 'faculty/faculty_dashboard.html')

def letter_upload(request):
    return render(request, 'student/cc1.html')

def index(request):
    return render(request, 'index.html')

# @csrf_exempt
@csrf_protect
def login_view(request):
    if not request.method == "POST":
        return render(request, 'login.html')

    # for POST (login method)
    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request, email, password)

    if user is None:
        # Handle invalid credentials
        return render(request, 'login.html', {'error_message': 'Invalid email or password'})
    login(request, user)
    role = determine_role_from_email(email)
    return redirect(request.GET.get('next', f'/{role}/dashboard/'))


def signup_view(request):
    if not request.method == "POST":
        return render(request, 'sign-up.html')
    
    # for POST (sign-up method)
    email = request.POST['email']
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    full_name = request.POST['full_name']

    if password != confirm_password:
        messages.error(request, "Passwords do not match")
        return render(request, 'sign-up.html')
    
    role = determine_role_from_email(email)

    # Role specific fields are obtained
    department = request.POST.get('department')
    graduation_year = None
    designation = None

    if role=='faculty':
        designation = request.POST.get('designation')
    elif role=='student':
        graduation_year = request.POST.get('graduation_year')

    result = register_user(email, password, full_name, department, graduation_year)

    if result['success']:
        login(request, result['user'])
        messages.success(request, f"Welcome {full_name}!")
        return redirect(f'{role}/dashboard')
    else:
        messages.error(request, f"Error {result['error']}")
        return render(request, 'sign-up.html')
    
