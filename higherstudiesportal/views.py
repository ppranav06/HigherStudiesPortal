from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

import logging

from .models import Student, Faculty, RecommendationRequest
from .utils.supabase_auth import determine_role_from_email, register_user, get_supabase_uuid
from .utils.supabase_storage import upload_file_to_bucket

#@login_required # decorator enforce after auth is set up

def type_user(request):
    """Function to get the type of user logged in"""
    if not request.user.is_authenticated:
        return None # support not found yet

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
    print("DEBUG: USER TYPE IS", user_type)
    return user_type

@login_required
def lor_application_student(request):
    if type_user(request) != 'student':
        raise PermissionDenied()
    
    # Query all faculty members to display in the dropdown
    faculties = Faculty.objects.all()
    return render(request, 'student/lor_application.html', {
        'faculties': faculties
    })

@login_required
def lor_tracking_student(request):
    if type_user(request) != 'student':
        raise PermissionDenied()
    
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
def letter_upload(request):
    if type_user(request) != 'student':
        raise PermissionDenied()
    return render(request, 'student/cc1.html')

@login_required
def dashboard_student(request):
    if type_user(request) != 'student':
        raise PermissionDenied()
    return render(request, 'student/student_dashboard.html')

@login_required
def dashboard_faculty(request):
    if type_user(request) != 'faculty':
        raise PermissionDenied()
    return render(request, 'faculty/faculty_dashboard.html')

@login_required
def f_verify(request):
    if type_user(request) != 'faculty':
        raise PermissionDenied()
    return render(request, 'faculty/f_verify.html')

@login_required
def f_student_list(request):
    if type_user(request) != 'faculty':
        raise PermissionDenied()
    return render(request, 'faculty/f_student_list.html')

def index(request):
    # current_user = request.user
    # if not current_user:
        return redirect('/login')


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
        # designation = request.POST.get('designation')
        designation = 'Associate Professor'
    elif role=='student':
        # graduation_year = request.POST.get('graduation_year')
        graduation_year = 2027

    result = register_user(email=email,
        password=password,
        full_name=full_name,
        department=department,
        graduation_year=graduation_year,
        designation=designation
    ) 
    # even if values are hardcoded, this check is again done at supabase_auth backend, so it doesn't matter for now
    # CHANGE LATER ^^^^^ (fix html)

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
    

logger = logging.getLogger(__name__)

@login_required
@require_POST
def upload_admission_letter(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)  # Assuming you have a Student model linked to the user
        
        # Get current user
        student_id = get_supabase_uuid(django_user=user) # Getting the supabase UUID from the Django user object
        
        # Extract file from request
        if 'admission_letter' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        file = request.FILES['admission_letter']
        
        # Validate file type
        if not file.name.endswith('.pdf'):
            return JsonResponse({"error": "Only PDF files are allowed"}, status=400)
        record_id = request.POST.get('record_id')
               
        upload_file_to_bucket(file_object=file,
                              bucket_name='admission_letters',
                              record_id=record_id,
                              student_id=student_id,
                              university_name=request.POST.get('university_name'),
                              program_name=request.POST.get('program_name'),
                              admission_date=request.POST.get('admission_date'),
                              logger=logger
                              )
        
        # Update the admission_records table with the file path
        # Note: This assumes the user is already creating or has created an admission record
        # You may need to adjust this logic based on your application flow
        
        # Option 1: If creating a new record along with the upload
        # db_response = supabase.table('admission_records').insert({
        #     'student_id': student_id,
        #     'university_name': request.POST.get('university_name', ''),  # You might want to get these values from the form
        #     'program_name': request.POST.get('program_name', ''),
        #     'letter_file_path': file_path
        # }).execute()
        
        # Option 2: If updating an existing record
        # Get the record ID from the request if available

    except Exception as e:
        logger.exception(f"Error in upload_admission_letter: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def submit_lor_request(request):
    if type_user(request) != 'student':
        raise PermissionDenied()
    
    if request.method == 'POST':
        try:
            # Get the student object
            student = Student.objects.get(user=request.user)
            
            # Create LOR requests for each selected faculty
            for i in range(1, 4):  # For staff 1, 2, 3
                faculty_id = request.POST.get(f'faculty{i}_id')
                
                if faculty_id:  # Only process if faculty was selected
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
                        
                        # Get common form data
                        university_name = request.POST.get('university_name')
                        program_name = request.POST.get('program_name')
                        deadline = request.POST.get('deadline')
                        additional_notes = request.POST.get('additional_notes', '')
                        
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
                        messages.error(request, f"Selected faculty {faculty_id} not found")
                    
            return redirect('lor-tracking')
            
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
        
    # If not POST or if there was an error, redirect back to the form
    return redirect('student_lor')