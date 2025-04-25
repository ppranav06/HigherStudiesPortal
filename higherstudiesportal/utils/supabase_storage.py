""""
Supabase Storage

The interface for supabase buckets
"""


from django.conf import settings
from django.http import JsonResponse
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
import uuid
import logging

from higherstudiesportal.models import Student, Faculty, AdmissionRecord, CourseCompletionRequest

getURLSERVICEKEY = lambda: (settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_file_path(file_object, bucket_name, student_id):
    # Blunder alert: initially used bucket_id/student_id which raised rls issues
    user_folder = f"{student_id}"  
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{file_object.name}"
    
    # Full path for the file in the bucket
    file_path = f"{user_folder}/{unique_filename}"
    print("DEBUG: File path is ", file_path)
    return file_path

def insert_record_fileupload(supabaseClient, 
                             student_id,
                             student_uuid,
                             university_name, 
                             program_name, 
                             admission_date, 
                             file_path, 
                             record_id=None):  
    # Fixing UUID Exceptions here (converting the uuid to string)
    if isinstance(student_uuid, uuid.UUID):
        student_uuid = str(student_uuid)
    if isinstance(record_id, uuid.UUID):
        record_id = str(record_id)
    
    # Check if record_id is provided (for update) or None (for insert)
    if record_id:
        db_response = supabaseClient.table('admission_records').update({
            'letter_file_path': file_path,
            'updated_at': datetime.now().isoformat()
        }).eq('id', record_id).execute()
    else:
        # Handle the case where no record ID is provided
        # This could be a new record or you might fetch the latest record for this student
        
        print("DEBUG: NEW admission_record RECORD IS",{
            'student_id': student_uuid,
            'university_name': university_name,
            'program_name': program_name,
            'admission_date': admission_date,
            'letter_file_path': file_path
        })
        
        # Now insert into Supabase
        supabase_db_response = supabaseClient.table('admission_records').insert({
            'student_id': student_uuid,
            'university_name': university_name,
            'program_name': program_name,
            'admission_date': admission_date,
            'letter_file_path': file_path
        }).execute()

        django_db_response = AdmissionRecord.objects.create(
            student=Student.objects.get(id=student_id),
            university_name=university_name,
            program_name=program_name,
            admission_date=admission_date,
            letter_file_path=file_path
        )

        django_db_response_coursecompletion = CourseCompletionRequest.objects.create(
            student=Student.objects.get(id=student_id),
            certificate_file=file_path
        )
        # Log the Django ORM responses
        print("DEBUG: Django ORM response for admission_record:", django_db_response)
        print("DEBUG: Django ORM response for coursecompletion:", django_db_response_coursecompletion)
        # Log the Supabase response
        print("DEBUG: Supabase response for admission_record:", supabase_db_response)

    # return only the supabase response (for further actions)
    return supabase_db_response
    

def upload_file_to_bucket(file_object, bucket_name, 
                          student_id, student_uuid, university_name, program_name, admission_date, record_id,
                          logger):
    load_dotenv('.env')
    URL, KEY = getURLSERVICEKEY()
    supabase = create_client(URL,KEY)
    
    file_path = get_file_path(file_object, bucket_name, student_uuid)

    # Log incoming values for debugging
    logger.info(f"RECEIVED VALUES: university_name={university_name}, program_name={program_name}, admission_date={admission_date}")
    
    # Safety check for required fields
    if not university_name or not program_name or not admission_date:
        logger.error("Missing required fields: Some form values were not provided")
        return JsonResponse({
            "error": "Missing required fields. Please fill in university name, program name, and admission date."
        }, status=400)

    try:
        storage_response = supabase.storage.from_(bucket_name).upload(
            file_path, 
            file_object.read(),
            file_options={'content-type': file_object.content_type}
        )
        
        # Storage upload successful if we reach here
        logger.info(f"File uploaded successfully: {file_path}")
        
    except Exception as e:
        logger.error(f"Supabase upload error: {str(e)}")
        return JsonResponse({"error": f"Failed to upload file: {str(e)}"}, status=500)
    
    try:
        # Log what we're about to send to the database
        logger.info(f"Attempting DB insert with: student_id={student_uuid}, university={university_name}, program={program_name}, file_path={file_path}")
        
        supabase_db_response = insert_record_fileupload(supabase, 
                                student_id,
                                student_uuid, 
                                university_name, 
                                program_name, 
                                admission_date, 
                                file_path, 
                                record_id)
        
        # Debug log the complete response
        logger.info(f"DB Response type: {type(supabase_db_response)}")
        logger.info(f"DB Response raw: {supabase_db_response}")
        
        # Supabase responses typically have data and error attributes
        if hasattr(supabase_db_response, 'data'):
            logger.info(f"DB Response data: {supabase_db_response.data}")
        
        if hasattr(supabase_db_response, 'error') and supabase_db_response.error:
            logger.error(f"Database error from response object: {supabase_db_response.error}")
            return JsonResponse({
                "success": True,
                "warning": f"File uploaded but database update failed: {supabase_db_response.error}",
                "file_path": file_path
            })
            
        return JsonResponse({
            "success": True,
            "file_path": file_path
        })
        
    except Exception as e:
        logger.error(f"Database update error: {str(e)}")
        logger.exception("Full exception details:")  # This logs the full traceback
        return JsonResponse({
            "success": True,
            "warning": f"File uploaded but database update failed: {str(e)}",
            "file_path": file_path
        })