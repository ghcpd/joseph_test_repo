(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const table = $('#dataset-table');
    if (table.length) {
      table.DataTable({
        pageLength: 10,
        responsive: true,
        lengthChange: false,
        order: [],
        language: {
          search: 'Search records:',
        },
      });
    }
  });
})();
