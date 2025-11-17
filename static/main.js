(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.getElementById('data-table');
    if (tableEl && typeof window.jQuery !== 'undefined') {
      const $table = window.jQuery(tableEl);
      if (!$table.hasClass('dataTable')) {
        $table.DataTable({
          responsive: true,
          pageLength: 10,
        });
      }
    }
  });
})();

function renderCharts(data) {
  if (typeof Plotly === 'undefined' || !data) {
    return;
  }

  const topReposEl = document.getElementById('chart-top-repos');
  if (topReposEl) {
    Plotly.newPlot(
      topReposEl,
      [
        {
          x: data.top_repos.labels,
          y: data.top_repos.values,
          type: 'bar',
          marker: { color: '#0d6efd' },
        },
      ],
      {
        margin: { t: 40, l: 50, r: 20, b: 80 },
        xaxis: { title: 'Repository' },
        yaxis: { title: 'PR Count' },
      },
      { responsive: true }
    );
  }

  const timeSeriesEl = document.getElementById('chart-time-series');
  if (timeSeriesEl) {
    Plotly.newPlot(
      timeSeriesEl,
      [
        {
          x: data.time_series.labels,
          y: data.time_series.values,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#198754' },
        },
      ],
      {
        margin: { t: 40, l: 50, r: 20, b: 80 },
        xaxis: { title: 'Date' },
        yaxis: { title: 'PR Count' },
      },
      { responsive: true }
    );
  }

  const closingIssuesEl = document.getElementById('chart-closing-issues');
  if (closingIssuesEl) {
    Plotly.newPlot(
      closingIssuesEl,
      [
        {
          labels: data.closing_issue_distribution.labels,
          values: data.closing_issue_distribution.values,
          type: 'pie',
          marker: { colors: ['#0d6efd', '#6f42c1', '#20c997', '#ffc107', '#dc3545'] },
        },
      ],
      {
        margin: { t: 40, l: 20, r: 20, b: 40 },
      },
      { responsive: true }
    );
  }

  const prMonthsEl = document.getElementById('chart-pr-months');
  if (prMonthsEl) {
    Plotly.newPlot(
      prMonthsEl,
      [
        {
          x: data.pr_month_histogram.labels,
          y: data.pr_month_histogram.values,
          type: 'bar',
          marker: { color: '#fd7e14' },
        },
      ],
      {
        margin: { t: 40, l: 50, r: 20, b: 80 },
        xaxis: { title: 'Month' },
        yaxis: { title: 'PR Count' },
      },
      { responsive: true }
    );
  }

  const topLabelsEl = document.getElementById('chart-top-labels');
  if (topLabelsEl) {
    Plotly.newPlot(
      topLabelsEl,
      [
        {
          x: data.top_labels.labels,
          y: data.top_labels.values,
          type: 'bar',
          marker: { color: '#6c757d' },
        },
      ],
      {
        margin: { t: 40, l: 50, r: 20, b: 80 },
        xaxis: { title: 'Label' },
        yaxis: { title: 'Usage Count' },
      },
      { responsive: true }
    );
  }
}
