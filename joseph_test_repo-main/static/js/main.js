$(document).ready(function () {
  const datasetButtons = $("[data-dataset]");
  const tableElement = $("#dataset-table");
  const repoFilterInput = $("#repo-filter");
  const datasetTitle = $("#dataset-title");
  const tableWrapper = $("#table-wrapper");
  const summaryElements = $("[data-summary]");

  if (!tableElement.length) {
    return;
  }

  const initialDataset = tableElement.data("dataset");
  const initialFields = tableElement.data("fields");
  const initialRecords = tableElement.data("records");
  const titles = tableElement.data("titles");

  let dataTable = null;

  function buildColumns(fields) {
    const columns = fields.map((field) => ({
      data: field,
      title: titles[field] || field.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      defaultContent: "N/A",
    }));
    columns.push({
      data: "detail_url",
      title: "Details",
      orderable: false,
      render: function (data) {
        if (!data) {
          return "N/A";
        }
        return `<a href="${data}" class="btn btn-sm btn-outline-primary">View</a>`;
      },
    });
    return columns;
  }

  function renderTable(datasetName, fields, records) {
    tableElement.data("dataset", datasetName);
    tableElement.data("fields", fields);
    tableElement.data("records", records);

    const columns = buildColumns(fields);
    if (dataTable) {
      dataTable.clear();
      dataTable.rows.add(records);
      dataTable.draw();
    } else {
      dataTable = tableElement.DataTable({
        data: records,
        columns,
        responsive: true,
        pageLength: 5,
      });
    }
  }

  function loadDataset(datasetName) {
    const repoFilter = repoFilterInput.val();
    const params = new URLSearchParams();
    if (repoFilter) {
      params.append("repo", repoFilter);
    }
    const query = params.toString();
    const url = query ? `/api/${datasetName}?${query}` : `/api/${datasetName}`;
    fetch(url)
      .then((response) => response.json())
      .then((payload) => {
        renderTable(datasetName, payload.fields, payload.records);
        datasetTitle.text(dataset_titles[datasetName] || datasetName);
        datasetButtons.removeClass("active");
        datasetButtons.filter(`[data-dataset="${datasetName}"]`).addClass("active");
        tableWrapper.removeClass("d-none");
        updateSummaryCounts(repoFilter);
      })
      .catch(() => {
        tableWrapper.addClass("d-none");
      });
  }

  function updateSummaryCounts(repoFilter) {
    const params = new URLSearchParams();
    if (repoFilter) {
      params.append("repo", repoFilter);
    }
    const query = params.toString();
    const url = query ? `/api/summary?${query}` : `/api/summary`;
    fetch(url)
      .then((response) => response.json())
      .then((payload) => {
        const counts = payload.counts || {};
        summaryElements.each(function () {
          const dataset = $(this).data("summary");
          if (dataset && dataset in counts) {
            $(this).text(counts[dataset]);
          }
        });
      });
  }

  datasetButtons.on("click", function () {
    const dataset = $(this).data("dataset");
    loadDataset(dataset);
  });

  $("#repo-filter-form").on("submit", function (event) {
    event.preventDefault();
    const activeDataset = tableElement.data("dataset") || initialDataset;
    loadDataset(activeDataset);
  });

  if (initialDataset && initialFields && initialRecords) {
    renderTable(initialDataset, initialFields, initialRecords);
  }

  updateSummaryCounts(repoFilterInput.val());
});
