from django.shortcuts import render

def lor_application_student(request):
    return render(request, 'lor_application.html')

def dashboard_student(request):
    return render(request, 'student_dashboard.html')

def dashboard_faculty(request):
    return render(request, 'faculty_dashboard.html')

def letter_upload(request):
    return render(request, 'cc1.html')

def index(request):
    return render(request, 'index.html')