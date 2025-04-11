
from django import template
from higherstudiesportal.models import Student, Faculty

register = template.Library()

@register.filter
def student_exists(user):
    return Student.objects.filter(user=user).exists()

@register.filter
def faculty_exists(user):
    return Faculty.objects.filter(user=user).exists()