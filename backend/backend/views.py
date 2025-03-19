from django.shortcuts import render

def lor_application_student(request):
    return render(request, 'lor_application.html')

def dashboard_student(request):
    return render(request, 'student_dashboard.html')

def dashboard_faculty(request):
    return render(request, 'faculty_dashboard.html')