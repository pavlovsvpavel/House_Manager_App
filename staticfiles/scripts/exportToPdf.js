/**
 * "Save as PDF" for the report pages.
 *
 * Renders `.report-results` with html2canvas-pro and lays the canvas
 * across A4 pages with jsPDF — the pipeline the html2pdf bundle used,
 * with the multi-page pagination kept. The bundle's html2canvas 1.4.1
 * cannot parse oklch()/color-mix() (every design-token color since the
 * Phase 4 migration), which made the export fail silently; html2canvas-pro
 * supports modern color functions.
 *
 * Pagination is row-safe: the fixed-height slicing cut rows in half at
 * page boundaries, so pages now break only between the atomic blocks
 * (details cards row, table header, body/footer rows) measured in the
 * capture clone, and continuation pages repeat the table header.
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
        let metrics = null;
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

                    // Row-safe pagination needs the atomic blocks' layout.
                    // html2canvas-pro renders this exact clone next, so the
                    // rects measured here (clone laid out at the forced
                    // viewport and capture width) are the capture's layout.
                    const base = results.getBoundingClientRect();
                    const rel = function (el, kind) {
                        const r = el.getBoundingClientRect();
                        return { kind: kind, top: r.top - base.top, bottom: r.bottom - base.top };
                    };
                    const blocks = [];
                    const details = results.querySelector('.details-wrapper');
                    if (details) {
                        blocks.push(rel(details, 'details'));
                    }
                    results.querySelectorAll('.report-table thead, .report-table tbody tr, .report-table tfoot tr')
                        .forEach(function (el) {
                            blocks.push(rel(el, el.tagName === 'THEAD' ? 'thead' : 'row'));
                        });
                    metrics = { blocks: blocks };
                },
            });
        } finally {
            labelled.forEach(function (pair) { pair[0].setAttribute('data-label', pair[1]); });
        }

        const imgWidth = A4.width - MARGIN * 2;
        const pxPerCm = canvas.width / imgWidth;
        const pageHeight = A4.height - MARGIN * 2;
        const pageContentPx = pageHeight * pxPerCm;

        // --- Row-safe pagination ------------------------------------------
        // Fixed-height slicing cut rows in half at page boundaries. Pages
        // now break only at block boundaries (cards row, table header,
        // body/footer rows), and continuation pages repeat the table
        // header on top.
        const scale = canvas.width / 794;
        const blocks = (metrics ? metrics.blocks : []).map(function (b) {
            return { kind: b.kind, top: b.top * scale, bottom: b.bottom * scale };
        });
        if (!blocks.length) {
            blocks.push({ kind: 'page', top: 0, bottom: canvas.height });
        }
        const theadBlock = blocks.find(function (b) { return b.kind === 'thead'; });
        const theadTop = theadBlock ? theadBlock.top : 0;
        const theadH = theadBlock ? theadBlock.bottom - theadBlock.top : 0;

        const pages = [];
        let idx = 0;
        while (idx < blocks.length) {
            // A continuation page that starts with a table row repeats the
            // header strip above it (and reserves its height).
            const repeatedThead = pages.length > 0 && blocks[idx].kind === 'row' && theadH > 0;
            const reserved = repeatedThead ? theadH : 0;
            const startIdx = idx;
            while (idx < blocks.length) {
                // Fit check uses the block's actual extent from the page
                // start, so inter-block margins/gaps count too and the
                // page slice never exceeds the printable height.
                if (blocks[idx].bottom - blocks[startIdx].top > pageContentPx - reserved) {
                    break;
                }
                idx += 1;
            }
            // A single block taller than a page (not reachable for table
            // rows) gets its own page and clips — never blocks the rest.
            if (idx === startIdx) {
                idx += 1;
            }
            pages.push({
                start: blocks[startIdx].top,
                end: idx < blocks.length ? blocks[idx].top : canvas.height,
                repeatedThead: repeatedThead,
            });
        }

        const pdf = new jspdf.jsPDF({unit: 'cm', format: 'a4', orientation: 'portrait'});
        for (let page = 0; page < pages.length; page++) {
            const seg = pages[page];
            const segH = seg.end - seg.start;
            const repeatedH = seg.repeatedThead ? theadH : 0;
            const outH = segH + repeatedH;

            // Each page is drawn from the full-height capture: the header
            // strip (continuations only) plus this page's block range.
            const out = document.createElement('canvas');
            out.width = canvas.width;
            out.height = Math.max(1, Math.round(outH));
            const ctx = out.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, out.width, out.height);
            if (repeatedH) {
                ctx.drawImage(canvas,
                    0, Math.round(theadTop), canvas.width, Math.round(theadH),
                    0, 0, canvas.width, Math.round(theadH));
            }
            ctx.drawImage(canvas,
                0, Math.round(seg.start), canvas.width, Math.round(segH),
                0, Math.round(repeatedH), canvas.width, Math.round(segH));

            if (page > 0) {
                pdf.addPage();
            }
            pdf.addImage(
                out.toDataURL('image/jpeg', 0.98),
                'JPEG',
                MARGIN,
                MARGIN,
                imgWidth,
                outH / pxPerCm
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
