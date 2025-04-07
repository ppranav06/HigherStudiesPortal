from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

# @login_required # enforce after auth is set up
def lor_application_student(request):
    return render(request, 'student/lor_application.html')

def lor_tracking_student(request):
    return render(request, 'student/lor_tracking.html')

def dashboard(request):
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

def login_view(request):
    if not request.method == "POST":
        return render(request, 'login.html')

    # for POST (login method)
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username, password)

    if user is not None:
        login(request, user)
        return redirect(request.GET.get('next', 'student/dashboard/'))
    else:
            # Handle invalid credentials
            return render(request, 'login.html', {'error_message': 'Invalid username or password'})
    

