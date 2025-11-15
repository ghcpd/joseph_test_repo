(function () {
  function formatCellValue(value) {
    if (value === null || value === undefined || value === '') {
      return 'N/A';
    }
    if (Array.isArray(value)) {
      return value.length ? value.join(', ') : '[]';
    }
    if (typeof value === 'object') {
      try {
        return JSON.stringify(value);
      } catch (error) {
        return 'Object';
      }
    }
    return value;
  }

  function buildDetailLink(dataset, record, meta) {
    const keyField = (meta && meta.key_field) || 'id';
    const keyValue = record && record[keyField];
    if (!keyValue) {
      return 'N/A';
    }
    const href = `/dataset/${dataset}/${encodeURIComponent(keyValue)}`;
    return `<a class="btn btn-sm btn-outline-primary" href="${href}">View</a>`;
  }

  async function fetchDataset(dataset, repoFilter) {
    const url = new URL(`/api/${dataset}`, window.location.origin);
    if (repoFilter) {
      url.searchParams.set('repo', repoFilter);
    }
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) {
      throw new Error('Failed to fetch dataset');
    }
    return response.json();
  }

  function renderTable(dataset, payload, meta, tableElement) {
    const fields = (meta && meta.display_fields && meta.display_fields.length)
      ? meta.display_fields
      : Object.keys(payload.data[0] || {});
    const data = payload.data || [];

    if ($.fn.DataTable.isDataTable(tableElement)) {
      tableElement.DataTable().destroy();
    }

    const theadRow = tableElement.find('thead tr');
    theadRow.empty();
    fields.forEach((field) => {
      theadRow.append(`<th>${field}</th>`);
    });
    theadRow.append('<th>Details</th>');

    const tbody = tableElement.find('tbody');
    tbody.empty();

    data.forEach((record) => {
      const row = $('<tr></tr>');
      fields.forEach((field) => {
        row.append(`<td>${formatCellValue(record[field])}</td>`);
      });
      row.append(`<td>${buildDetailLink(dataset, record, meta)}</td>`);
      tbody.append(row);
    });

    tableElement.DataTable({
      responsive: true,
      pageLength: 10,
      lengthMenu: [5, 10, 25, 50],
      language: {
        search: 'Search records:',
        emptyTable: 'No records available',
      },
    });
  }

  async function initDatasetTable() {
    if (!window.datasetMeta || !window.selectedDataset) {
      return;
    }
    const tableEl = $('#dataset-table');
    if (!tableEl.length) {
      return;
    }
    const dataset = window.selectedDataset;
    const meta = window.datasetMeta[dataset];
    try {
      const payload = await fetchDataset(dataset, window.repoFilter || '');
      renderTable(dataset, payload, meta, tableEl);
    } catch (error) {
      console.error('Failed to render dataset table', error);
    }
  }

  document.addEventListener('DOMContentLoaded', initDatasetTable);
})();
