# GitHub PR/Issue Flask App

This Flask app loads GitHub PR/Issue JSONL datasets and provides a dashboard, detail pages, and interactive visualizations.

Screenshots:
- Homepage (dataset table): https://github.com/user-attachments/assets/d0541c2c-739e-4457-b6ac-d9554643594b
- Visualize page: https://github.com/user-attachments/assets/b2c7bfae-b628-42c5-aa5d-3815682e9c34
- Detail page: https://github.com/user-attachments/assets/5fa28f79-a89a-49e8-a703-365a6c7820f1


## Structure
- app.py: Flask application
- templates/: Jinja2 templates (Bootstrap, DataTables, Plotly)
- input_data/: Input JSONL files (pr_issue_single.jsonl, pr_detail.jsonl, issue_detail.jsonl)
- output_data/: Output JSONL file (merged_data.jsonl)
- requirements.txt: Python dependencies

## Run locally

Set a custom port (optional):
  PORT=5056 python app.py

Key routes:
- / — Dashboard with dataset counts and tables
- /dataset/<dataset_name>/<record_id> — Detail view with related data
- /visualize — Interactive charts (filter with ?repo=<owner/repo>)
- /api/<dataset_name> — JSON for a dataset, supports ?repo=<owner/repo>

1. Create a virtual environment (optional)
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   python app.py
4. Open http://127.0.0.1:5000/ in your browser

## Notes
- Large datasets are loaded into memory at startup. Ensure sufficient memory.
- Use the Visualize page to filter by repository via the `?repo=` query parameter.
