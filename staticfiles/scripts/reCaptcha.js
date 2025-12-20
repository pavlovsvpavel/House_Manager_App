document.addEventListener('DOMContentLoaded', function () {
    const SITE_KEY = '6LcoTSwrAAAAAI6dKKYaOU9VQ7nrKzKbOMEtYrxr';

    function handleRecaptcha(formId, inputId, actionName) {
        const form = document.getElementById(formId);
        const tokenInput = document.getElementById(inputId);

        if (form && tokenInput) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();

                grecaptcha.ready(function () {
                    grecaptcha.execute(SITE_KEY, {action: actionName}).then(function (token) {
                        tokenInput.value = token;
                        form.submit();
                    });
                });
            });
        }
    }

    handleRecaptcha('registerForm', 'recaptchaTokenRegister', 'register');

    handleRecaptcha('loginForm', 'recaptchaTokenLogin', 'login');
});