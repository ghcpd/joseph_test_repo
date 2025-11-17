# PR & Issue Analytics Dashboard

This project provides a lightweight Flask web application for exploring and visualizing GitHub pull request and issue data. The application loads JSONL datasets produced by GitHub API calls and an integration script, then exposes a responsive dashboard with interactive tables and charts.

## Project Structure

```
├── app.py                 # Flask application entry point
├── data/                  # Helper utilities for data loading and aggregation
├── input_data/            # Source JSONL datasets from the GitHub API
├── output_data/           # Merged JSONL dataset created by integrate_pr_issue.py
├── static/                # CSS and JavaScript assets (Bootstrap, DataTables integration)
├── templates/             # Jinja2 templates powering the UI
├── tests/                 # Automated tests for critical routes
├── requirements.txt       # Python dependencies required for the app and tests
└── README.md              # Project documentation and usage guide
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the Flask server**

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   The dashboard will be available at <http://127.0.0.1:5000/>. Navigate to the **Visualizations** page to explore Plotly charts or use the home page to browse dataset tables.

3. **Execute tests**

   ```bash
   pytest
   ```

## Features

- Loads four JSONL datasets on startup and exposes them via `/api/<dataset>` endpoints.
- Responsive Bootstrap UI with summary cards and dataset selection controls.
- DataTables.js integration for client-side table search, sorting, and pagination.
- Detail pages for each record with linked, related data across datasets.
- Plotly-powered charts with optional repository filtering via query parameters.
- Cached aggregations ensure fast visualization updates.

## Data Sources

Sample JSONL files are provided in `input_data/` and `output_data/` to demonstrate the application. Replace them with datasets generated from the GitHub API to visualize your repository data.

## Notes

- Missing fields render as `N/A` in the interface to keep the UI clear.
- All charts fall back to an informative message when the requested filter produces no results.
- The project uses only runtime dependencies required for the application and tests.
