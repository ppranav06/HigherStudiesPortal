// Javascript for validation and file upload

document.addEventListener('DOMContentLoaded', function() {
    // const admitCardInput = document.getElementById("admitCard");
    // const errorAdmit = document.getElementById("errorAdmit");
    const admissionLetterInput = document.getElementById("admissionLetter");
    const errorAdmission = document.getElementById("errorAdmission");
    const uploadBtn = document.getElementById("uploadBtn");

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

    function checkUploadEligibility() {
        // const isAdmitValid = validateFile(admitCardInput, errorAdmit); // currently sticking to one file, later acoommodate more
        const isAdmissionValid = validateFile(admissionLetterInput, errorAdmission);
        // uploadBtn.disabled = !(isAdmitValid && isAdmissionValid); // don't use
        uploadBtn.disabled = !(isAdmissionValid);
    }

    // admitCardInput.addEventListener("change", checkUploadEligibility);
    admissionLetterInput.addEventListener("change", checkUploadEligibility);

        // Add event listener for upload button
    uploadBtn.addEventListener("click", uploadFile);
    
    function uploadFile() {
        const file = admissionLetterInput.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('admission_letter', file);
        
        // Get CSRF token from cookie
        const csrftoken = getCookie('csrftoken');
        
        // Display loading state
        uploadBtn.disabled = true;
        uploadBtn.textContent = "Uploading...";
        
        fetch('/upload_admission_letter/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            return response.json();
        })
        .then(data => {
            // Show success message
            uploadBtn.textContent = "Upload Complete!";
            uploadBtn.style.backgroundColor = "#4CAF50";
            
            // Optionally redirect or update UI
            setTimeout(() => {
                uploadBtn.textContent = "Upload Files";
                uploadBtn.disabled = false;
                // Clear the file input
                admissionLetterInput.value = "";
            }, 3000);
        })
        .catch(error => {
            errorAdmission.textContent = "Upload failed: " + error.message;
            uploadBtn.textContent = "Upload Files";
            uploadBtn.disabled = false;
        });
    }
    
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
});