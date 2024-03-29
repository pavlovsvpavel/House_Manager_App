function saveAsPDF() {
    // Get the content of the div element with class "report-results"
    const reportResultsElement = document.querySelector('.report-results');

    // Check if the element exists
    if (reportResultsElement) {
        // Create a new html2pdf instance
        const element = reportResultsElement;
        const opt = {
            margin: 0.5,
            filename: 'report.pdf',
            image: {type: 'jpeg', quality: 0.98},
            html2canvas: {scale: 2},
            jsPDF: {unit: 'cm', format: 'letter', orientation: 'portrait'}
        };

        // Generate PDF from HTML element
        html2pdf().set(opt).from(element).save();
    } else {
        console.error('Element with class "report-results" not found.');
    }
}
