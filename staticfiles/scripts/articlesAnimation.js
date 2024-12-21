document.addEventListener("DOMContentLoaded", () => {
    const articles = document.querySelectorAll("#articles-section article");

    const observer = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add("article-visible");
                        observer.unobserve(entry.target);
                    }, index * 300);
                }
            });
        },
        {
            root: null,
            rootMargin: "0px",
            threshold: 0.1
        }
    );

    articles.forEach((article) => {
        observer.observe(article);
    });
});

