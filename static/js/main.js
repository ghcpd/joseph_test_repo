document.addEventListener('DOMContentLoaded', () => {
  const datasetButtons = document.querySelectorAll('[data-dataset-button]');
  const tables = document.querySelectorAll('.data-table');
  const tableContainers = document.querySelectorAll('.dataset-table');
  const tableInstances = new Map();

  tables.forEach((table) => {
    const datasetName = table.getAttribute('data-dataset');
    const instance = window.jQuery(table).DataTable({
      paging: true,
      searching: true,
      responsive: true,
      lengthChange: false,
      pageLength: 5,
    });
    tableInstances.set(datasetName, instance);
  });

  const showDataset = (datasetName) => {
    tableContainers.forEach((container) => {
      if (container.getAttribute('data-dataset') === datasetName) {
        container.classList.add('active');
        const instance = tableInstances.get(datasetName);
        if (instance) {
          instance.columns.adjust().draw();
        }
      } else {
        container.classList.remove('active');
      }
    });

    datasetButtons.forEach((btn) => {
      if (btn.getAttribute('data-dataset-button') === datasetName) {
        btn.classList.add('btn-primary');
        btn.classList.remove('btn-outline-primary');
      } else {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline-primary');
      }
    });
  };

  datasetButtons.forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const datasetName = btn.getAttribute('data-dataset-button');
      showDataset(datasetName);
      const url = new URL(window.location.href);
      url.searchParams.set('dataset', datasetName);
      window.history.replaceState({}, '', url.toString());
    });
  });

  const defaultDataset = document.body.getAttribute('data-default-dataset');
  if (defaultDataset) {
    showDataset(defaultDataset);
  }
});
