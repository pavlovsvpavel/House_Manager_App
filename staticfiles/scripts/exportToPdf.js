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

        // html2canvas(-pro) has no container-query support: its CSS parser
        // hoists the mobile card-view block (td flex, td ::before
        // data-labels, hidden tfoot) onto ALL widths, so exports captured
        // on phones came out as "cards with headers on every row" — and
        // it resolves content: attr(...) against the original element,
        // so stripping the attribute in onclone is not enough. Remove the
        // data-labels from the live DOM for the duration of the capture
        // and force the print table geometry via the onclone override.
        const labelled = Array.from(element.querySelectorAll('[data-label]'))
            .map(function (el) { return [el, el.getAttribute('data-label')]; });
        labelled.forEach(function (pair) { pair[0].removeAttribute('data-label'); });

        let canvas;
        try {
            canvas = await html2canvas(element, {
                scale: 2,
                // Exports are print artifacts: always render the light
                // "paper" theme and the desktop table layout, no matter
                // which theme or viewport the export was triggered from.
                backgroundColor: '#ffffff',
                // Desktop-wide clone viewport so media queries never
                // collapse on phones.
                windowWidth: 1200,
                onclone: function (doc) {
                    // Scripts do nothing for a static render — but the
                    // theme bootstrap re-runs in the clone and re-applies
                    // the dark attribute after the removal below.
                    doc.querySelectorAll('script').forEach(function (s) { s.remove(); });

                    // Light tokens: dark mode is scoped to
                    // [data-theme="dark"] on <html>; removing the
                    // attribute restores paper colors.
                    doc.documentElement.removeAttribute('data-theme');

                    const results = doc.querySelector('.report-results');
                    if (!results) {
                        return;
                    }
                    // A4 at 96dpi — the fixed capture width every export shares.
                    results.style.width = '794px';

                    const override = doc.createElement('style');
                    override.textContent = [
                        '.report-table-wrap { container-type: normal !important; width: 100% !important; }',
                        '.report-table thead { display: table-header-group !important; }',
                        '.report-table tfoot { display: table-footer-group !important; }',
                        '.report-table tr { display: table-row !important; border: none !important; background: transparent !important; padding: 0 !important; }',
                        '.report-table th, .report-table td { display: table-cell !important; border-bottom: 1px solid var(--line) !important; }',
                        '.report-table th::before, .report-table td::before { content: none !important; }',
                    ].join('\n');
                    doc.head.appendChild(override);
                },
            });
        } finally {
            labelled.forEach(function (pair) { pair[0].setAttribute('data-label', pair[1]); });
        }

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
        // Slug comes from the URL path, not the (translated) page title:
        // .../reports/monthly/ -> monthly-bills-reports,
        // .../reports/other/   -> other-bills-reports.
        // A Cyrillic title would collapse to '' under the ASCII \w slug.
        const path = window.location.pathname;
        let slug;
        if (path.includes('/reports/other/')) {
            slug = 'other-bills-reports';
        } else if (path.includes('/reports/monthly/')) {
            slug = 'monthly-bills-reports';
        } else {
            // Fallback for future report pages: slugify the title.
            const title = document.querySelector('.reports .section-title');
            slug = (title ? title.textContent : 'report')
                .trim().toLowerCase()
                .replace(/[^\w]+/g, '-')
                .replace(/^-+|-+$/g, '') || 'report';
        }
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
