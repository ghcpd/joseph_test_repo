# PR/Issue Data Viewer

A Flask-based web application for processing and visualizing GitHub PR and Issue data from JSONL files.

## Features

### Data Loading
- Loads four JSONL files into memory at startup:
  - `input_data/pr_issue_single.jsonl` - PR search results with closing issue information
  - `input_data/pr_detail.jsonl` - Detailed pull request information
  - `input_data/issue_detail.jsonl` - Detailed issue information  
  - `output_data/merged_data.jsonl` - Integrated PR-issue data
- Creates indexed lookups for fast data retrieval
- Handles missing fields gracefully

### Homepage Dashboard (`/`)
- Summary cards showing total records in each dataset
- Dataset switcher with tabs for easy navigation
- Searchable, sortable tables using DataTables.js
- Responsive design for mobile and desktop
- Quick action links for exploration

### Dataset Detail Pages (`/dataset/<dataset_name>/<record_id>`)
- Complete record view with all fields
- Related data linking between PR and Issue records
- JSON pretty-printing for complex nested objects
- Navigation between records
- Breadcrumb navigation

### Interactive Visualizations (`/visualize`)
- **Merged Data Charts:**
  - Bar chart of top 10 repositories by PR count
  - Time series of PR creation dates
- **PR Issue Single Charts:**
  - Distribution of closing issue counts per repository
- **PR Detail Charts:** 
  - Histogram of PRs by month/year
- **Issue Detail Charts:**
  - Top 10 labels used across issues
- Repository filtering via URL query parameters
- Built with Chart.js for interactive features

### JSON API Endpoints
- `/api/<dataset_name>` - Returns filtered dataset data
- `/api/chart_data/<chart_type>` - Returns chart data with filtering
- Supports pagination and repository filtering
- Cached aggregations for performance

### Technical Features
- Flask + Jinja2 + Bootstrap 5 responsive design
- Client-side table search with DataTables.js
- Error handling for missing data
- Mobile-friendly interface
- Copy-to-clipboard functionality for code blocks

## Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   ```bash
   python app.py
   ```

3. **Access the Web Interface:**
   - Open http://localhost:5000 in your browser
   - Dashboard: http://localhost:5000/
   - Visualizations: http://localhost:5000/visualize

## Data Structure

The application expects the following JSONL files:

### Input Data Files
- `input_data/pr_issue_single.jsonl` - GitHub issue search results with PR information
- `input_data/pr_detail.jsonl` - Detailed PR data from GitHub API
- `input_data/issue_detail.jsonl` - Detailed issue data from GitHub API

### Output Data Files  
- `output_data/merged_data.jsonl` - Integrated data created by `integrate_pr_issue.py`

## API Usage

### Get Dataset Data
```
GET /api/<dataset_name>?repo=<repo_filter>&page=<page>&per_page=<per_page>
```

### Get Chart Data
```
GET /api/chart_data/<chart_type>?repo=<repo_filter>
```

Available chart types:
- `top_repos` - Top repositories by PR count
- `pr_timeline` - PR creation timeline
- `closing_issue_distribution` - Closing issue distribution
- `pr_monthly` - PR creation by month
- `top_labels` - Top issue labels

## Project Structure

```
.
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── templates/                     # Jinja2 templates
│   ├── base.html                 # Base template with Bootstrap
│   ├── homepage.html             # Dashboard page
│   ├── detail.html               # Record detail page
│   └── visualize.html            # Visualization page
├── input_data/                   # Input JSONL files
│   ├── pr_issue_single.jsonl
│   ├── pr_detail.jsonl
│   └── issue_detail.jsonl
├── output_data/                  # Generated data files
│   └── merged_data.jsonl
└── integrate_pr_issue.py         # Data integration script
```

## Dependencies

- Flask 3.0.0 - Web framework
- Jinja2 3.1.2 - Template engine
- Bootstrap 5.3.0 - CSS framework
- DataTables.js 1.13.6 - Table functionality
- Chart.js - Interactive charts
- jQuery 3.7.0 - JavaScript library

## Performance Considerations

- Data is loaded into memory at startup for fast access
- Table pagination limits displayed records for performance
- Chart data is cached and computed on-demand
- Responsive design optimized for various screen sizes

## Browser Compatibility

- Modern browsers supporting HTML5 and ES6
- Mobile responsive design
- Tested on Chrome, Firefox, Safari, and Edge