document.addEventListener("DOMContentLoaded", function() {
    const scrollToTopBtn = document.querySelector(".scrollToTopBtn");
    if (scrollToTopBtn) {
        const rootElement = document.documentElement;

        function handleScroll() {
            // Do something on scroll - 0.10 is the percentage the page has to scroll before the button appears
            const scrollTotal = rootElement.scrollHeight - rootElement.clientHeight;
            if ((rootElement.scrollTop / scrollTotal) > 0.10) {
                // Show button
                scrollToTopBtn.classList.add("showBtn")
            } else {
                // Hide button
                scrollToTopBtn.classList.remove("showBtn")
            }
        }

        function scrollToTop() {
            // Scroll to top logic
            rootElement.scrollTo({
                top: 0,
                behavior: "smooth"
            })
        }

        scrollToTopBtn.addEventListener("click", scrollToTop);
        document.addEventListener("scroll", handleScroll);
    }
});