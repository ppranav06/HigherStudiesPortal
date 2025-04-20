from django.db import models
# from django.contrib.auth.models import AbstractUser
import uuid
from django.contrib.auth.models import User
class SupabaseUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    supabase_uuid = models.UUIDField(unique=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.supabase_uuid}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100)
    graduation_year = models.IntegerField()
    
    def __str__(self):
        return self.user.get_full_name()

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    
    def __str__(self):
        return self.user.get_full_name()

class RecommendationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purpose = models.TextField()
    university_name = models.CharField(max_length=200, blank=True)
    program_name = models.CharField(max_length=200, blank=True)
    deadline = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AdmissionRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    university_name = models.CharField(max_length=200)
    program_name = models.CharField(max_length=200)
    admission_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    is_scholarship = models.BooleanField(default=False)
    scholarship_details = models.TextField(blank=True)
    letter_file_path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)