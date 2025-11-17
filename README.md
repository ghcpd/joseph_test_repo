# GitHub PR and Issue Dashboard

This repository provides a Flask-based dashboard for exploring relationships between GitHub pull requests and issues. It ingests multiple JSONL exports and offers tabular exploration, searchable data tables, and interactive charts.

## Features

- Loads four JSONL datasets on startup and keeps them in memory for fast lookup
- Dashboard with summary counts, dataset selector, and searchable tables powered by DataTables.js
- Detail view for each record with related data links between pull requests, issues, and merged rows
- Visualization page with Chart.js powered charts for merged data, PR detail, issue detail, and PR issue search results
- JSON API endpoints for each dataset to power interactive components and external integrations
- Responsive UI built with Bootstrap 5

## Project Structure

```
├── app.py
├── data
│   ├── input_data
│   │   ├── issue_detail.jsonl
│   │   ├── pr_detail.jsonl
│   │   └── pr_issue_single.jsonl
│   └── output_data
│       └── merged_data.jsonl
├── requirements.txt
├── static
│   ├── css
│   │   └── styles.css
│   └── js
│       └── app.js
└── templates
    ├── base.html
    ├── dataset_detail.html
    ├── index.html
    └── visualize.html
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the Flask application**

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   The dashboard will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

3. **Explore the datasets**
   - Use the homepage tabs to switch between datasets.
   - Click the “View” button to inspect a record with related entries.
   - Navigate to `/visualize` for interactive charts.

## API Endpoints

JSON endpoints are available for each dataset and support optional repository filtering via `?repo=`:

- `/api/pr_issue`
- `/api/pr_detail`
- `/api/issue_detail`
- `/api/merged_data`

Example request filtering by repository:

```
GET /api/merged_data?repo=octocat/hello-world
```

## Visualization Summary

- **Merged data:** Top repositories by PR count and PR creation timeline
- **PR issue search results:** Distribution of closing issues by repository
- **PR details:** Histogram of pull requests grouped by month/year
- **Issue details:** Most frequently used labels across issues

## Data Provenance

Sample JSONL files are adapted from the GitHub REST API. The merged dataset showcases how pull requests and issues relate across the inputs. Review `data/input_data` and `data/output_data` to inspect the structures.

## License

This project is provided as-is for demonstration purposes.
