# PR/Issue Data Visualization Tool

A Flask-based web application for processing and visualizing GitHub pull request and issue data from JSONL files.

## Features

- **Data Loading**: Loads four JSONL datasets (pr_issue_single, pr_detail, issue_detail, merged_data) into memory at startup
- **Dashboard**: Interactive homepage with summary statistics and switchable dataset views
- **Data Tables**: Searchable, sortable tables using DataTables.js for each dataset
- **Detail Pages**: Individual record views with related data links across datasets
- **Visualizations**: Interactive charts using Chart.js showing:
  - Top repositories by PR count
  - PR creation timeline
  - Closing issue distribution
  - PR histogram by month
  - Top issue labels
- **Repository Filtering**: Filter visualizations by repository name
- **JSON API**: RESTful endpoints for accessing filtered dataset data
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5

## Project Structure

```
.
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── input_data/                     # Input JSONL files
│   ├── pr_issue_single.jsonl      # PR-issue search results
│   ├── pr_detail.jsonl            # Detailed PR information
│   └── issue_detail.jsonl         # Detailed issue information
├── output_data/                    # Output JSONL files
│   └── merged_data.jsonl          # Merged PR-issue data
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                  # Base template with navigation
│   ├── index.html                 # Dashboard homepage
│   ├── detail.html                # Record detail page
│   └── visualize.html             # Visualization page
└── static/                         # Static assets
    ├── css/
    │   └── style.css              # Custom CSS styles
    └── js/                         # (Reserved for custom JS if needed)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd joseph_test_repo
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify data files**:
   Ensure the following JSONL files exist:
   - `input_data/pr_issue_single.jsonl`
   - `input_data/pr_detail.jsonl`
   - `input_data/issue_detail.jsonl`
   - `output_data/merged_data.jsonl`

## Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. **Available routes**:
   - `/` - Dashboard with dataset selector
   - `/visualize` - Interactive charts and visualizations
   - `/visualize?repo=owner/repo1` - Filtered visualizations
   - `/dataset/<dataset_name>/<record_id>` - Individual record details
   - `/api/<dataset_name>` - JSON API endpoint
   - `/api/<dataset_name>?repo=owner/repo1` - Filtered JSON API

## Usage Guide

### Dashboard

The dashboard displays:
- Summary cards showing total records in each dataset
- Tabs to switch between datasets
- Searchable, sortable tables with DataTables.js
- Links to view detailed information for each record

### Detail Pages

Detail pages show:
- All fields of a selected record
- Related data from other datasets
- Quick navigation links

### Visualizations

The visualization page provides:
- Interactive charts for all datasets
- Repository filter dropdown
- Various chart types (bar, line, doughnut) using Chart.js

### API Endpoints

Access data programmatically:

```bash
# Get all PR detail records
curl http://localhost:5000/api/pr_detail

# Get filtered issue detail records
curl http://localhost:5000/api/issue_detail?repo=owner/repo1
```

Response format:
```json
{
  "dataset": "pr_detail",
  "count": 10,
  "data": [...]
}
```

## Data Files

### pr_issue_single.jsonl
Modified from GitHub Issues Search API. Contains:
- `id`: Record ID
- `repo`: Repository name
- `pr_number`: Pull request number
- `title`: PR title
- `created_at`: Creation timestamp
- `state`: PR state (open/closed)
- `closing_issue`: Number of issues closed

### pr_detail.jsonl
From GitHub Pull Requests API. Contains:
- `id`: Record ID
- `repo`: Repository name
- `pr_number`: Pull request number
- `title`: PR title
- `body`: PR description
- `created_at`, `updated_at`, `merged_at`: Timestamps
- `state`: PR state
- `user`: Author username
- `additions`, `deletions`: Code changes
- `changed_files`: Number of files changed

### issue_detail.jsonl
From GitHub Issues API. Contains:
- `id`: Record ID
- `repo`: Repository name
- `issue_number`: Issue number
- `title`: Issue title
- `body`: Issue description
- `created_at`, `updated_at`, `closed_at`: Timestamps
- `state`: Issue state
- `user`: Reporter username
- `labels`: Array of labels
- `comments`: Comment count

### merged_data.jsonl
Produced by integrate_pr_issue.py. Contains:
- `repo`: Repository name
- `issue_number`: Issue number
- `issue_title`: Issue title
- `pull_number`: PR number
- `pr_title`: PR title
- `created_at`: PR creation time
- `merged_at`: PR merge time
- `issue_created_at`: Issue creation time

## Technical Details

### Technologies Used

- **Backend**: Flask 3.0.0
- **Frontend**: Bootstrap 5, jQuery
- **Data Processing**: pandas 2.1.4
- **Tables**: DataTables.js 1.13.6
- **Charts**: Chart.js 4.4.0
- **Template Engine**: Jinja2 3.1.2

### Caching

The application implements in-memory caching for computed aggregations to improve performance:
- Visualization data is cached per repository filter
- Cache is stored in a Python dictionary
- Cache keys include filter parameters

### Error Handling

- Missing fields display as "N/A" in the UI
- Non-existent datasets return 404 errors
- Invalid record IDs show "Record not found" messages
- Date parsing errors fall back to displaying raw values

## Development

To modify the application:

1. **Add new routes**: Edit `app.py` and add Flask route handlers
2. **Update templates**: Modify files in `templates/` directory
3. **Add styles**: Edit `static/css/style.css`
4. **Add JavaScript**: Create files in `static/js/` directory

### Debug Mode

The application runs in debug mode by default when started with `python app.py`. To disable:

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## License

This project is provided as-is for educational and demonstration purposes.

## Support

For issues or questions, please refer to the repository's issue tracker.
