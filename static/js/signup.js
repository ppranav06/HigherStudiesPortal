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
    // Student pattern: letters followed by numbers then @uni.edu.in
    const studentPattern = /^[a-zA-Z]+[\d]{7}+@ssn\.edu\.in$/;
    // Faculty pattern: just letters then @uni.edu.in
    const facultyPattern = /^[a-zA-Z]+@ssn\.edu\.in$/;
    
    const studentFields = document.querySelectorAll('.student-field');
    const facultyFields = document.querySelectorAll('.faculty-field');
    
    // Hide all role-specific fields first
    studentFields.forEach(field => field.style.display = 'none');
    facultyFields.forEach(field => field.style.display = 'none');
    
    // Show appropriate fields based on email
    if (studentPattern.test(email)) {
        studentFields.forEach(field => field.style.display = 'block');
    } else if (facultyPattern.test(email)) {
        facultyFields.forEach(field => field.style.display = 'block');
    }
}