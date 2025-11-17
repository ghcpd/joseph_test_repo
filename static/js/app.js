document.addEventListener("DOMContentLoaded", function () {
  const datasetTable = document.getElementById("dataset-table");
  if (datasetTable && window.jQuery && typeof jQuery.fn.DataTable === "function") {
    jQuery(datasetTable).DataTable({
      paging: true,
      searching: true,
      ordering: true,
      pageLength: 10,
      lengthChange: false,
      language: {
        search: "Search dataset:",
        emptyTable: "No data available for this selection",
      },
    });
  }
});
