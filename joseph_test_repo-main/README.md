# PR & Issue Dashboard

This project provides a Flask-based dashboard for exploring and visualizing merged GitHub pull request and issue data. It loads four JSON Lines files, offers interactive tables with DataTables, and renders multiple charts using Plotly.

## Project Structure

```
.
├── app.py
├── data/
│   ├── input_data/
│   │   ├── issue_detail.jsonl
│   │   ├── pr_detail.jsonl
│   │   └── pr_issue_single.jsonl
│   └── output_data/
│       └── merged_data.jsonl
├── templates/
│   ├── base.html
│   ├── detail.html
│   ├── index.html
│   └── visualize.html
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
└── README.md
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the app**

   ```bash
   flask --app app run
   ```

   The dashboard will be available at http://127.0.0.1:5000/.

3. **Explore**
   - Home: interactive tables with search, sort, and repo filtering.
   - Visualizations: chart-based insights with optional repo-level filtering.
   - Detail pages: drill into a single record with related data links.

## API Endpoints

Each dataset has a JSON API endpoint supporting optional repo filtering via query parameters.

- `/api/pr_issue`
- `/api/pr_detail`
- `/api/issue_detail`
- `/api/merged_data`

Example:

```
GET /api/merged_data?repo=octo/repo1
```

## Notes

- All charts use cached aggregations for fast loading.
- DataTables provides client-side search and pagination.
- The included JSONL files contain representative sample data. Replace them with real exports to explore other repositories.
