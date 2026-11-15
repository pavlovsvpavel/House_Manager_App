/**
 * "Save as PDF" for the report pages.
 *
 * Renders `.report-results` with html2canvas-pro and lays the canvas
 * across A4 pages with jsPDF — the pipeline the html2pdf bundle used,
 * with the multi-page pagination kept. The bundle's html2canvas 1.4.1
 * cannot parse oklch()/color-mix() (every design-token color since the
 * Phase 4 migration), which made the export fail silently; html2canvas-pro
 * supports modern color functions.
 */
(function () {
    'use strict';

    const A4 = {width: 21, height: 29.7}; // cm
    const MARGIN = 0.5;                   // cm

    async function saveAsPDF() {
        const element = document.querySelector('.report-results');
        if (!element) {
            console.error('Element with class "report-results" not found.');
            return;
        }

        const canvas = await html2canvas(element, {scale: 2});

        const imgWidth = A4.width - MARGIN * 2;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        const pageHeight = A4.height - MARGIN * 2;
        const pages = Math.max(1, Math.ceil(imgHeight / pageHeight));

        const pdf = new jspdf.jsPDF({unit: 'cm', format: 'a4', orientation: 'portrait'});
        for (let page = 0; page < pages; page++) {
            if (page > 0) {
                pdf.addPage();
            }
            pdf.addImage(
                canvas.toDataURL('image/jpeg', 0.98),
                'JPEG',
                MARGIN,
                MARGIN - page * pageHeight,
                imgWidth,
                imgHeight
            );
        }

        pdf.save(reportFilename());
    }

    function reportFilename() {
        // "Monthly bills - reports" + ?year=2026&month=10 ->
        // monthly-bills-reports-2026-10.pdf
        const title = document.querySelector('.reports .section-title');
        const slug = (title ? title.textContent : 'report')
            .trim().toLowerCase()
            .replace(/[^\w]+/g, '-')
            .replace(/^-+|-+$/g, '');
        const params = new URLSearchParams(window.location.search);
        const period = [params.get('year'), params.get('month')].filter(Boolean);
        return period.length ? `${slug}-${period.join('-')}.pdf` : `${slug}.pdf`;
    }

    // Loaded with defer — the DOM is parsed when this runs.
    const pdfBtn = document.getElementById('generatePdf');
    if (pdfBtn) {
        pdfBtn.addEventListener('click', function () {
            saveAsPDF().catch(function (err) {
                console.error('PDF export failed:', err);
            });
        });
    }
})();
