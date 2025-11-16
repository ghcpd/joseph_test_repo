# PR & Issue Dashboard

This project is a Flask-based web dashboard for exploring pull request and issue data gathered from GitHub. Four JSONL datasets are loaded on start-up and exposed through a rich UI featuring searchable tables, record-level detail pages, and interactive visualizations.

## Features

- **Data ingestion**: Loads data at start-up from `data/input_data/` and `data/output_data/`.
- **Dashboard**: Summary counts, dataset switching buttons, and searchable/sortable tables powered by DataTables.
- **Detail pages**: Comprehensive record layouts with cross-linked related entries.
- **Visualizations**: Plotly charts highlighting repository activity, timelines, issue closure statistics, PR cadence, and label usage.
- **Filter support**: Visualizations can be filtered by repository via query parameter or form control.
- **JSON APIs**: `/api/<dataset_name>` endpoints provide dataset records and cached aggregations for client-side charting.

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   The server will start at `http://127.0.0.1:5000/`.

## Data Overview

| Dataset | File | Description |
|---------|------|-------------|
| `pr_issue` | `data/input_data/pr_issue_single.jsonl` | PR search results with optional `closing_issue` metadata. |
| `pr_detail` | `data/input_data/pr_detail.jsonl` | Detailed pull request information including linked issue numbers. |
| `issue_detail` | `data/input_data/issue_detail.jsonl` | Detailed issue metadata with labels. |
| `merged_data` | `data/output_data/merged_data.jsonl` | Merged PR–issue entries combining key fields. |

## API Endpoints

- `GET /api/pr_issue`
- `GET /api/pr_detail`
- `GET /api/issue_detail`
- `GET /api/merged_data`

Each endpoint supports an optional `repo` query parameter and returns both matching records and cached aggregations used for visualization rendering.

## Testing

Automated tests are not included; run `python -m compileall app.py` to perform a basic syntax check.

## License

This project is provided for demonstration and evaluation purposes.
