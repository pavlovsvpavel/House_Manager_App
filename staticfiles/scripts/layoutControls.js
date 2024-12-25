$(document).ready(function() {
  $('#generatePdf').click(function() {
    if (window.innerWidth <= 600) {
      $('.details-wrapper').toggleClass('row-mobile');

      // Add timeout to restore column layout after a short delay (adjust delay as needed)
      setTimeout(function() {
        if (window.innerWidth <= 600) {
          $('.details-wrapper').removeClass('row-mobile');
        }
      }, 3000);
    }
  });
});