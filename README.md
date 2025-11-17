# PR and Issue Insights Dashboard

This project is a Flask-based web dashboard for exploring sample GitHub pull request and issue data. It loads JSONL datasets describing pull requests, issues, and merged relationships, and presents them through searchable tables, detailed record pages, and interactive visualizations.

## Features

- Loads four JSONL datasets at startup and keeps them in memory for fast navigation.
- Responsive Bootstrap interface with summary cards, dataset selectors, and searchable/sortable tables powered by DataTables.
- Detailed record views showing all fields along with related data links.
- Interactive Plotly charts for visualizing repository activity trends, PR creation timelines, closing issue distributions, PR volume by month, and top issue labels.
- REST-style JSON API endpoints for each dataset (`/api/<dataset_name>`), supporting optional repository filtering for integration with the charts.
- Cached aggregations behind the visualization page for efficient rendering.

## Project Structure

```
app.py                # Flask application
input_data/           # Sample JSONL input datasets (pr_issue, pr_detail, issue_detail)
output_data/          # Sample merged dataset
static/               # CSS and JavaScript assets
templates/            # Jinja2 templates
requirements.txt      # Python dependencies
README.md             # Project documentation
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the application**

   ```bash
   flask --app app run
   ```

   The dashboard will be available at <http://127.0.0.1:5000/>.

3. **Explore the data**

   - The homepage provides dataset summaries and searchable tables.
   - Click a record's “View” button to inspect all fields and related entries.
   - Visit `/visualize` for interactive charts; add `?repo=owner/name` to filter by repository.

## API Endpoints

- `GET /api/pr_issue`
- `GET /api/pr_detail`
- `GET /api/issue_detail`
- `GET /api/merged_data`

Each endpoint accepts an optional query parameter `repo=owner/name` to filter results by repository.

## Testing

The application is designed for interactive exploration. You can ensure the code compiles by running:

```bash
python -m compileall app.py
```

## Screenshots

Screenshots of the UI are included in the pull request discussion to illustrate the dashboard and visualization pages.
