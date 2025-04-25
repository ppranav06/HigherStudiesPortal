from django.conf import settings # use lazy import for settings (more aligned with other code)
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db import models # for join query equivalents in django's ORM
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User  # Add this import

import logging
import json
from datetime import datetime, timedelta
import re
import os

from .models import Student, Faculty, RecommendationRequest, AdmissionRecord, CourseCompletionRequest
from .utils.supabase_auth import determine_role_from_email, register_user, get_supabase_uuid
from .utils.supabase_storage import upload_file_to_bucket
from .utils.binomial_heap import BinomialHeap  # adjust import if needed
from .utils.supabase_auth import get_supabase_client

def index(request):
    # return render(request, 'index.html') # problem for later, need to add index
    return redirect('/login')

######################################################################
# Validation functions

def type_user(request):
    """Function to get the type of user logged in"""
    if not request.user.is_authenticated:
        return None

    current_user = request.user
    try:
        stud = Student.objects.get(user=current_user)
        user_type='student' 
    except Student.DoesNotExist:
        try:
            facul = Faculty.objects.get(user=current_user)
            user_type='faculty'
        except Faculty.DoesNotExist:
            user_type = 'notanyofthese'
    # print("DEBUG: USER TYPE IS", user_type)
    return user_type

def type_user_with_userobj(user):
    """Function to get the type of user logged in"""
    if not user.is_authenticated:
        return None

    current_user = user
    try:
        stud = Student.objects.get(user=current_user)
        user_type='student' 
    except Student.DoesNotExist:
        try:
            facul = Faculty.objects.get(user=current_user)
            user_type='faculty'
        except Faculty.DoesNotExist:
            user_type = 'notanyofthese'
    # print("DEBUG: USER TYPE IS", user_type)
    return user_type

def is_faculty(user):
    return user.is_authenticated and type_user_with_userobj(user) == 'faculty'

def is_student(user):
    return user.is_authenticated and type_user_with_userobj(user) == 'student'

def is_admin(user):
    """Check if user's email is in the allowed admin emails list"""
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip().lower() for email in admin_emails if email.strip()]
    
    # # Debug printing
    # print("\n=== Admin Check Debug ===")
    # print(f"User email: {user.email}")
    # print(f"User email (lowercase): {user.email.lower()}")
    # print(f"Admin emails from env: {os.getenv('ADMIN_EMAILS')}")
    # print(f"Processed admin emails: {admin_emails}")
    # print(f"Is user authenticated: {user.is_authenticated}")
    # print(f"Is email in admin list: {user.email.lower() in admin_emails}")
    # print("=======================\n")
    
    return user.is_authenticated and user.email.lower() in admin_emails

######################################################################
# Student Views here

@login_required
@user_passes_test(is_student)
def lor_application_student(request):
    # Query all faculty members to display in the dropdown
    faculties = Faculty.objects.all()
    return render(request, 'student/lor_application.html', {
        'faculties': faculties
    })

@login_required
@user_passes_test(is_student)
def lor_tracking_student(request):
    try:
        # Get the student's recommendation requests
        student = Student.objects.get(user=request.user)

        lor_requests = RecommendationRequest.objects.filter(student=student).order_by('-created_at')
        return render(request, 'student/lor_tracking.html', {
            'lor_requests': lor_requests
        })
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found")
        return redirect('student_dashboard')

@login_required
@user_passes_test(is_student)
def letter_upload(request):
    return render(request, 'student/cc1.html')

@login_required
@user_passes_test(is_student)
def dashboard_student(request):
    return render(request, 'student/student_dashboard.html')

@login_required
@user_passes_test(is_student)
def verification_tracking_student(request):
    try:
        student = Student.objects.get(user=request.user)
        # Raw SQL approach (with connection) (am I dumb???)
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.id, a.university_name, a.program_name, a.admission_date, 
                       cc.status, a.created_at 
                FROM higherstudiesportal_admissionrecord a
                JOIN higherstudiesportal_coursecompletionrequest cc 
                    ON cc.student_id = a.student_id
                WHERE a.student_id = %s
                ORDER BY a.created_at DESC
            """, [student.id])
            
            certificates = [
                {
                    'id': row[0],
                    'university_name': row[1],
                    'program_name': row[2],
                    'admission_date': row[3],
                    'status': row[4],
                    'created_at': row[5]
                }
                for row in cursor.fetchall()
            ]
        
        return render(request, 'student/cc_verification.html', {'certificates': certificates})
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found")
        return redirect('student_dashboard')

######################################################################
# Faculty Views here

@login_required
@user_passes_test(is_faculty)
def dashboard_faculty(request):
    try:
        faculty = Faculty.objects.get(user=request.user)
        
        # Get recent LOR requests for this faculty member
        recent_requests = RecommendationRequest.objects.filter(
            faculty=faculty
        ).select_related(
            'student', 
            'student__user'
        ).annotate(
            student_name=models.functions.Concat(
                models.F('student__user__first_name'), 
                models.Value(' '), 
                models.F('student__user__last_name'),
                output_field=models.CharField()
            )
        ).values(
            'student_name',
            'university_name',
            'status'
        ).order_by('-created_at')[:5]  # Get only the 5 most recent requests
        
        return render(request, 'faculty/faculty_dashboard.html', {
            'recent_requests': recent_requests
        })
    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found")
        return redirect('login')

@login_required
@user_passes_test(is_faculty)
def f_student_list(request):
    students = Student.objects.all()
    return render(request, 'faculty/f_student_list.html', {'students': students})

@login_required
@user_passes_test(is_faculty)
def approveLOR(request):
    """View to approve or reject LOR requests"""
    
    # Get the faculty user
    faculty = Faculty.objects.get(user=request.user)
    
    # Using raw SQL-like query with Django ORM to match your requested join pattern ('F' from django.db.models)
    lor_requests = RecommendationRequest.objects.filter(
        faculty=faculty
    ).select_related(
        'student', 
        'student__user'
    ).annotate(
        student_name=models.functions.Concat(
            models.F('student__user__first_name'), 
            models.Value(' '), 
            models.F('student__user__last_name'),
            output_field=models.CharField()
        )
    ).values(
        'id',
        'student_id',
        'student_name',
        'status'
    ).order_by('-created_at')
    
    # This approximates the SQL query:
    #   SELECT CONCAT(a.first_name||' '||a.last_name) as student_name, 
    #          lor.student_id as student_id, 
    #          lor.status as status 
    #   FROM higherstudiesportal_recommendationrequest lor
    #   JOIN higherstudiesportal_student s on s.id=lor.student_id
    #   JOIN auth_user a on a.id=s.user_Id;
    #   WHERE lor.faculty_id = faculty.id
    #   ORDER BY lor.created_at DESC;

    print(lor_requests)
    return render(request, 'faculty/f_verify.html', {'lor_requests': lor_requests})

@login_required
@user_passes_test(is_faculty)
@csrf_exempt
def update_lor_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            new_status = data.get('status')
            
            if not request_id or not new_status:
                return JsonResponse({'success': False, 'error': 'Missing required parameters'})
                
            # Validate status value
            if new_status not in ['Pending', 'Verified', 'Rejected']:
                return JsonResponse({'success': False, 'error': 'Invalid status value'})
                
            # Update the LOR request status
            lor_request = RecommendationRequest.objects.get(id=request_id)
            lor_request.status = new_status
            lor_request.save()
            
            return JsonResponse({'success': True})
            
        except RecommendationRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'LOR request not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


######################################################################
# Login and Signup
# @csrf_exempt
@csrf_protect
def login_view(request):
    if not request.method == "POST":
        return render(request, 'login.html')

    # for POST (login method)
    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request=request, username=email, password=password)

    if user is None:
        # Handle invalid credentials
        return render(request, 'login.html', {'error_message': 'Invalid email or password'})
    
    login(request=request, user=user)
    
    # Check if user is admin using the is_admin function
    if is_admin(user):
        return redirect('admin_dashboard')
        
    # For other users, use role-based redirection
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
    
    # Check if trying to create an admin account
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    if email in admin_emails:
        messages.error(request, "Unauthorized account creation")
        return render(request, 'sign-up.html')
    
    role = determine_role_from_email(email)

    # Role specific fields are obtained
    department = request.POST.get('department')
    graduation_year = None
    designation = None

    if role=='faculty':
        designation = 'Associate Professor'
    elif role=='student':
        graduation_year = 2027

    result = register_user(email=email,
        password=password,
        full_name=full_name,
        department=department,
        graduation_year=graduation_year,
        designation=designation
    )

    if result['success']:
        login(request, result['user'], backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Welcome {full_name}!")
        return redirect(f'/login')
    else:
        messages.error(request, f"Error {result['error']}")
        return render(request, 'sign-up.html')
    

def logout_view(request):
    logout(request)
    return redirect('/accounts/login')
    

######################################################################
# Main functions: 
# - Apply LOR / Track status
# - Upload admission letter


logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def upload_admission_letter(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
        
        # Get current user
        student_id = student.id
        # Get UUID from Supabase (auth)
        student_uuid = get_supabase_uuid(django_user=user)
        
        # Log the incoming request data for debugging
        logger.info(f"Received form data: {dict(request.POST)}")
        logger.info(f"Files: {dict(request.FILES)}")
        
        # Extract file from request
        if 'admission_letter' not in request.FILES:
            logger.error("No file provided in request")
            return JsonResponse({"error": "No file provided"}, status=400)
        
        file = request.FILES['admission_letter']
        
        # Validate file type
        if not file.name.endswith('.pdf'):
            logger.error(f"Invalid file type: {file.name}")
            return JsonResponse({"error": "Only PDF files are allowed"}, status=400)
        
        # Extract form data with defaults to avoid None values
        university_name = request.POST.get('university_name', '')
        if university_name:
            university_name = university_name.strip()
        
        program_name = request.POST.get('program_name', '')
        if program_name:
            program_name = program_name.strip()
        
        admission_date = request.POST.get('admission_date', '')
        if admission_date:
            admission_date = admission_date.strip()
        
        # Log the specific values we're trying to use
        logger.info(f"University name: '{university_name}'")
        logger.info(f"Program name: '{program_name}'")
        logger.info(f"Admission date: '{admission_date}'")
        
        # Validate required fields with detailed logging
        if not university_name:
            logger.error("Missing university name")
            return JsonResponse({"error": "University name is required"}, status=400)
        
        if not program_name:
            logger.error("Missing program name")
            return JsonResponse({"error": "Program name is required"}, status=400)
        
        if not admission_date:
            logger.error("Missing admission date")
            return JsonResponse({"error": "Admission date is required"}, status=400)
        
        record_id = request.POST.get('record_id')

        logger.info(f"All validations passed, calling upload_file_to_bucket with: university_name={university_name}, program_name={program_name}, admission_date={admission_date}")
        
        responseFromUploadFile = upload_file_to_bucket(
            file_object=file,
            bucket_name=settings.SUPABASE_BUCKET_NAME,
            record_id=record_id,
            student_id=student_id,
            student_uuid=student_uuid,
            university_name=university_name,
            program_name=program_name,
            admission_date=admission_date,
            logger=logger
        )
        
        return responseFromUploadFile

    except Exception as e:
        logger.exception(f"Error in upload_admission_letter: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(is_student)
def submit_lor_request(request):
    
    if request.method == 'POST':
        try:
            # Get the student object
            student = Student.objects.get(user=request.user)
            
            # Extract common form data
            university_name = request.POST.get('university_name')
            program_name = request.POST.get('program_name')
            deadline = request.POST.get('deadline')
            additional_notes = request.POST.get('additional_notes', '')
            
            # Get all faculty IDs from the POST data
            faculty_ids = []
            for key in request.POST:
                if key.startswith('faculty') and key.endswith('_id') and request.POST[key]:
                    faculty_ids.append(request.POST[key])
            
            if not faculty_ids:
                messages.warning(request, "Please select at least one faculty member.")
                return redirect('student_lor')
            
            # Process each selected faculty
            for faculty_id in faculty_ids:
                try:
                    faculty = Faculty.objects.get(id=faculty_id)
                    
                    # Check if a request already exists for this student-faculty pair
                    from .models import RecommendationRequest
                    existing_request = RecommendationRequest.objects.filter(
                        student=student,
                        faculty=faculty,
                        status__in=['pending', 'approved']
                    ).exists()
                    
                    if existing_request:
                        messages.warning(request, f"You already have an active LOR request with {faculty.user.get_full_name()}")
                        continue
                    
                    # Create the recommendation request
                    RecommendationRequest.objects.create(
                        student=student,
                        faculty=faculty,
                        status='pending',
                        university_name=university_name,
                        program_name=program_name,
                        deadline=deadline if deadline else None,
                        additional_notes=additional_notes
                    )
                    
                    messages.success(request, f"LOR request submitted to {faculty.user.get_full_name()}")
                
                except Faculty.DoesNotExist:
                    messages.error(request, f"Selected faculty (ID: {faculty_id}) not found")
                
            return redirect('lor-tracking')
            
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
        
    # If not POST or if there was an error, redirect back to the form
    return redirect('student_lor')

# binomial heap
def prioritized_requests(request):
    supabase = get_supabase_client()
    response = supabase.table("admission_records").select("*").execute()
    requests = response.data

    today = datetime.today().date()
    heap = BinomialHeap()

    for req in requests:
        admission_str = req.get("admission_date")
        if not admission_str:
            continue
        admission_date = datetime.strptime(admission_str, "%Y-%m-%d").date()
        days_left = (admission_date - today).days
        priority = max(days_left, 0)
        heap.insert(req, priority)

    sorted_requests = []
    while not heap.is_empty():
        sorted_requests.append(heap.extract_min())

    return JsonResponse(sorted_requests, safe=False)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    try:
        # Get statistics
        total_students = Student.objects.count()
        pending_verifications = CourseCompletionRequest.objects.filter(status='pending').count()

        # Get recent verification requests
        recent_verifications = CourseCompletionRequest.objects.select_related(
            'student__user'
        ).order_by('-created_at')[:5]

        context = {
            'total_students': total_students,
            'pending_verifications': pending_verifications,
            'recent_verifications': recent_verifications,
            'user': request.user
        }

        return render(request, 'admin/admin_dashboard.html', context)

    except Exception as e:
        print(f"\n=== Admin Dashboard Error ===")
        print(f"Error: {str(e)}")
        print("===========================\n")
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('login')

@login_required
@user_passes_test(is_admin)
def verify_certificate(request):
    """View to handle verification of course completion certificates"""
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        try:
            completion_request = CourseCompletionRequest.objects.get(id=request_id)
            
            if action == 'verify':
                completion_request.status = 'Verified'
            elif action == 'reject':
                completion_request.status = 'Rejected'
            
            completion_request.notes = notes
            completion_request.save()
            
            messages.success(request, f"Certificate {action}d successfully")
        except CourseCompletionRequest.DoesNotExist:
            messages.error(request, "Certificate request not found")
        
        return redirect('admin_dashboard')
    
    # Get all pending verification requests
    pending_requests = CourseCompletionRequest.objects.filter(
        status='Pending'
    ).select_related(
        'student',
        'student__user'
    ).order_by('-created_at')
    
    return render(request, 'admin/verify_certificate.html', {
        'pending_requests': pending_requests
    })

@login_required
@user_passes_test(is_admin)
def admin_student_list(request):
    """View to display list of all students for admin"""
    students = Student.objects.select_related('user').all()
    return render(request, 'admin/student_list.html', {'students': students})