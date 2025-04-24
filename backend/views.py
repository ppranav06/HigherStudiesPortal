from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Certificate

@login_required
def verification_tracking_student(request):
    if not request.user.is_student:
        return redirect('home')
    
    certificates = Certificate.objects.filter(student=request.user.student).order_by('-created_at')
    return render(request, 'student/cc_verification.html', {'certificates': certificates})
