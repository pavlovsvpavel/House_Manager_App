document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("togglePassword");
  const passwordField = document.getElementById("id_password");
  const toggleIcon = document.getElementById("toggleIcon");

  if (toggleButton && passwordField) {
    toggleButton.addEventListener("click", function () {
      const type = passwordField.type === "password" ? "text" : "password";
      passwordField.type = type;

      // Toggle icon class
      toggleIcon.classList.toggle("fa-eye");
      toggleIcon.classList.toggle("fa-eye-slash");
    });
  }
});


