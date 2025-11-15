$(document).ready(function () {
  if ($('#dataset-table').length) {
    $('#dataset-table').DataTable({
      pageLength: 10,
      ordering: true,
      responsive: true
    });
  }

  const repoSelect = document.getElementById('repo');
  if (repoSelect && repoSelect.form) {
    repoSelect.addEventListener('change', function () {
      repoSelect.form.submit();
    });
  }
});
