# PR-Issue Dashboard

This project provides a Flask-based dashboard and API for exploring relationships between pull requests and issues. It loads sample GitHub metadata from JSONL files and offers interactive tables and charts powered by DataTables.js and Plotly.

## Project Structure

```
.
├── app.py
├── input_data/
│   ├── pr_detail.jsonl
│   ├── pr_issue_single.jsonl
│   └── issue_detail.jsonl
├── output_data/
│   └── merged_data.jsonl
├── static/
│   ├── css/
│   │   └── custom.css
│   └── js/
│       └── app.js
├── templates/
│   ├── base.html
│   ├── detail.html
│   ├── index.html
│   └── visualize.html
└── tests/
    └── test_app.py
```

## Requirements

Install dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server with:

```bash
python app.py
```

The dashboard will be available at [http://localhost:5000](http://localhost:5000).

## Testing

Run the automated tests with:

```bash
python -m pytest
```

## Features

- Loads four JSONL datasets into memory at startup
- Interactive table explorer with client-side search, sorting, and filtering
- Detailed record view showing related records across datasets
- Visualizations for repository activity and issue/PR metadata
- JSON API endpoints backing UI and external integrations

## Environment

The repository includes sample data for demonstration purposes. Replace the contents of the `.jsonl` files with real GitHub export data to analyze your own projects.
