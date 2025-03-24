from django.shortcuts import render

def lor_application_student(request):
    return render(request, 'student/lor_application.html')

def dashboard_student(request):
    return render(request, 'student/student_dashboard.html')

def dashboard_faculty(request):
    return render(request, 'faculty/faculty_dashboard.html')

def letter_upload(request):
    return render(request, 'student/cc1.html')

def index(request):
    return render(request, 'index.html')