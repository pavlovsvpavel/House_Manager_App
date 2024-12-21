document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('togglePassword');
    const passwordId = toggleButton.dataset.passwordId;

    const passwordInput = document.getElementById(passwordId);

    if (passwordInput) {
        const parentDiv = passwordInput.closest('div');

        const toggleButton = document.getElementById('togglePassword');
        const toggleIcon = document.getElementById('toggleIcon');

        passwordInput.insertAdjacentElement('afterend', toggleButton);

        parentDiv.classList.add('password-container');
        toggleButton.classList.add('toggle-btn');

        toggleButton.addEventListener('click', function () {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            toggleIcon.classList.toggle('fa-eye-slash');
            toggleIcon.classList.toggle('fa-eye');
        });
    }
});


