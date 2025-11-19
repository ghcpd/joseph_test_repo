(function ($) {
  $(function () {
    const $table = $('#dataset-table');
    if ($table.length) {
      $table.DataTable({
        order: [],
        pageLength: 10,
        responsive: true,
      });

      $table.on('click', 'tbody tr', function (event) {
        if ($(event.target).closest('a, button').length) {
          return;
        }
        const href = $(this).data('href');
        if (href) {
          window.location.href = href;
        }
      });
    }
  });
})(jQuery);
