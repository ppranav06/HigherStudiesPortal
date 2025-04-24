// Javascript for validation and file upload

document.addEventListener('DOMContentLoaded', function() {
    const admissionLetterInput = document.getElementById("admissionLetter");
    const errorAdmission = document.getElementById("errorAdmission");
    const uploadBtn = document.getElementById("uploadBtn");
    const universityNameInput = document.getElementById("university_name");
    const programNameInput = document.getElementById("program_name");
    const admissionDateInput = document.getElementById("admission_date");

    function validateFile(input, errorElement) {
        if (!input.files.length) {
            errorElement.textContent = "";
            return false;
        }

        const file = input.files[0];
        const maxSize = 2 * 1024 * 1024; 

        if (file.type !== "application/pdf") {
            errorElement.textContent = "Only PDF files are allowed.";
            input.value = "";
            return false;
        }

        if (file.size > maxSize) {
            errorElement.textContent = "File size must be under 2MB.";
            input.value = "";
            return false;
        }

        errorElement.textContent = "";
        return true;
    }

    function checkAllFieldsValid() {
        const isAdmissionValid = validateFile(admissionLetterInput, errorAdmission);
        const isUniversityValid = universityNameInput.value.trim() !== "";
        const isProgramValid = programNameInput.value.trim() !== "";
        const isDateValid = admissionDateInput.value !== "";
        
        // Enable upload button only if all fields are valid
        uploadBtn.disabled = !(isAdmissionValid && isUniversityValid && isProgramValid && isDateValid);
    }

    // Add event listeners for all form fields
    admissionLetterInput.addEventListener("change", function() {
        validateFile(admissionLetterInput, errorAdmission);
        checkAllFieldsValid();
    });
    
    universityNameInput.addEventListener("input", checkAllFieldsValid);
    programNameInput.addEventListener("input", checkAllFieldsValid);
    admissionDateInput.addEventListener("change", checkAllFieldsValid);

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Add event listener for upload button
    uploadBtn.addEventListener('click', function() {
        // Get values and validate them again
        const file = admissionLetterInput.files[0];
        const universityName = universityNameInput.value;
        const programName = programNameInput.value;
        const admissionDate = admissionDateInput.value;
        
        console.log("Submitting values:", {
            universityName, 
            programName, 
            admissionDate
        });
        
        // Double check required fields
        if (!file) {
            errorAdmission.textContent = "Please select a file to upload";
            return;
        }
        
        if (!universityName || !programName || !admissionDate) {
            errorAdmission.textContent = "Please fill in all required fields";
            return;
        }
        
        const formData = new FormData();
        formData.append('admission_letter', file);
        formData.append('university_name', universityName);
        formData.append('program_name', programName);
        formData.append('admission_date', admissionDate);
        
        // Add this line to include the CSRF token in the FormData
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        
        // Add this after creating the FormData object
        console.log("FormData contents:");
        for (const pair of formData.entries()) {
            console.log(pair[0] + ': ' + (pair[1] instanceof File ? pair[1].name + ' (' + pair[1].size + ' bytes)' : pair[1]));
        }
        
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');
        
        // Display loading state
        uploadBtn.disabled = true;
        uploadBtn.textContent = "Uploading...";
        
        fetch('/upload_admission_letter/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
                // Do NOT set Content-Type here - the browser will set it with the right boundary for multipart/form-data
            },
            body: formData
        })
        .then(response => {
            console.log("Response status:", response.status);
            return response.json().then(data => ({
                status: response.status,
                body: data
            }));
        })
        .then(({status, body}) => {
            if (status >= 400) {
                throw new Error(body.error || "Upload failed");
            }
            
            // Show success message
            uploadBtn.textContent = "Upload Complete!";
            uploadBtn.style.backgroundColor = "#4CAF50";
            
            // Reset form after success
            setTimeout(() => {
                uploadBtn.textContent = "Upload Files";
                uploadBtn.disabled = false;
                uploadBtn.style.backgroundColor = ""; // Reset button color
                
                // Clear the form
                admissionLetterInput.value = "";
                universityNameInput.value = "";
                programNameInput.value = "";
                admissionDateInput.value = "";
                checkAllFieldsValid(); // Re-validate form
            }, 3000);
        })
        .catch(error => {
            console.error("Upload error:", error);
            errorAdmission.textContent = "Upload failed: " + error.message;
            uploadBtn.textContent = "Upload Files";
            uploadBtn.disabled = false;
        });
    });
    
    // Initial form validation
    checkAllFieldsValid();
});