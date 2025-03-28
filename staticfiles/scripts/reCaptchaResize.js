function resizeCaptcha() {
    const captchaElem = document.getElementsByClassName("g-recaptcha")[0];

    if (captchaElem) {
        const captchaWidth = captchaElem.children[0].offsetWidth;
        const parentWidth = captchaElem.parentElement.offsetWidth;

        // Calculate scale but prevent excessive scaling
        const scale = Math.min(parentWidth / captchaWidth, 1.0);

        // Apply scaling
        captchaElem.style.transform = "scale(" + scale + ")";
        captchaElem.style.transformOrigin = "0 0";

        // Adjust container height to prevent overlap
        const captchaHeight = captchaElem.children[0].offsetHeight * scale;
        captchaElem.style.height = captchaHeight + "px";
    }
}

// Ensure reCAPTCHA is ready before resizing
grecaptcha.ready(resizeCaptcha);

// Resize on window resize
window.addEventListener("resize", resizeCaptcha);

