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

from .supabase_auth import getURLKEY

def get_file_path(file_object, bucket_name, student_id):
    # Create a unique folder path for this user
    user_folder = f"{bucket_name}/{student_id}"
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{file_object.name}"
    
    # Full path for the file in the bucket
    file_path = f"{user_folder}/{unique_filename}"
    print("DEBUG: File path is ", file_path)
    return file_path

def insert_record_fileupload(supabaseClient, 
                             student_id, 
                             university_name, 
                             program_name, 
                             admission_date, 
                             file_path, 
                             record_id=None):  
    if record_id:
        db_response = supabaseClient.table('admission_records').update({
            'letter_file_path': file_path,
            'updated_at': datetime.now().isoformat()
        }).eq('id', record_id).execute()
    else:
        # Handle the case where no record ID is provided
        # This could be a new record or you might fetch the latest record for this student
        db_response = supabaseClient.table('admission_records').insert({
            'student_id': student_id,
            'university_name': university_name,
            'program_name': program_name,
            'admission_date': admission_date,
            'letter_file_path': file_path
        }).execute()

        return db_response
    

def upload_file_to_bucket(file_object, bucket_name, 
                          student_id, university_name, program_name, admission_date, record_id,
                          logger):
    load_dotenv('.env')
    URL, KEY = getURLKEY()
    supabase = create_client(URL,KEY)
    
    file_path = get_file_path(file_object, bucket_name, student_id)

    storage_response = supabase.storage.from_('documents').upload(
        file_path, 
        file_object.read(), # if file from requests, use file.read() to bring here
        file_options={'content-type': file_object.content_type}
    )

    if 'error' in storage_response:
        logger.error(f"Supabase upload error: {storage_response['error']}")
        return JsonResponse({"error": "Failed to upload file"}, status=500)
    
    db_response = insert_record_fileupload(supabase, 
                             student_id, 
                             university_name, 
                             program_name, 
                             admission_date, 
                             file_path, 
                             record_id)

    if 'error' in db_response:
        logger.error(f"Database update error: {db_response['error']}")
            # Even if DB update fails, the file was uploaded successfully
        return JsonResponse({
            "success": True,
            "warning": "File uploaded but database update failed",
            "file_path": file_path
        })

    return JsonResponse({
        "success": True,
        "file_path": file_path
    })