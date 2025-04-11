const signInBtnLink = document.querySelector(".signInBtn-link");
const signUpBtnLink = document.querySelector(".signUpBtn-link");
const wrapper = document.querySelector(".wrapper");
signUpBtnLink.addEventListener("click", () => {
  wrapper.classList.toggle("active");
});
signInBtnLink.addEventListener("click", () => {
  wrapper.classList.toggle("active");
});

function checkEmailType(email) {
  // Student pattern: letters followed by exactly 7 digits then @ssn.edu.in
  const studentPattern = /^[a-zA-Z]+\d{7}@ssn\.edu\.in$/;
  
  // Faculty pattern: just letters then @ssn.edu.in
  const facultyPattern = /^[a-zA-Z]+@ssn\.edu\.in$/;
  
  const studentFields = document.querySelectorAll('.student-field');
  const facultyFields = document.querySelectorAll('.faculty-field');
  const userTypeField = document.getElementById('userType');
  
  // Hide all role-specific fields first
  studentFields.forEach(field => field.style.display = 'none');
  facultyFields.forEach(field => field.style.display = 'none');
  
  // Show appropriate fields and set the userType field value based on email
  if (studentPattern.test(email)) {
    studentFields.forEach(field => field.style.display = 'block');
    if (userTypeField) userTypeField.value = 'student';
    return 'student';
  } else if (facultyPattern.test(email)) {
    facultyFields.forEach(field => field.style.display = 'block');
    if (userTypeField) userTypeField.value = 'faculty';
    return 'faculty';
  } else if (email && email.includes('@')) {
    // Invalid SSN email format
    return 'invalid';
  }
  
  return null; // No match or empty email
}

// Add an event listener to the email input field
document.addEventListener('DOMContentLoaded', function() {
  const emailField = document.getElementById('email');
  const messageBox = document.getElementById('messageBox');
  
  if (emailField) {
    emailField.addEventListener('blur', function() {
      const result = checkEmailType(this.value);
      
      // Clear any existing messages
      if (messageBox) messageBox.innerHTML = '';
      
      // Show message for invalid emails
      if (result === 'invalid') {
        if (messageBox) {
          messageBox.innerHTML = '<div class="error-message">Please use a valid SSN email address</div>';
        }
      }
    });
  }
});