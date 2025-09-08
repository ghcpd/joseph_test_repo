# GitHub PR/Issue Flask App

This Flask app loads GitHub PR/Issue JSONL datasets and provides a dashboard, detail pages, and interactive visualizations.

## Structure
- app.py: Flask application
- templates/: Jinja2 templates (Bootstrap, DataTables, Plotly)
- input_data/: Input JSONL files (pr_issue_single.jsonl, pr_detail.jsonl, issue_detail.jsonl)
- output_data/: Output JSONL file (merged_data.jsonl)
- requirements.txt: Python dependencies

## Run locally
1. Create a virtual environment (optional)
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   python app.py
4. Open http://127.0.0.1:5000/ in your browser

## Notes
- Large datasets are loaded into memory at startup. Ensure sufficient memory.
- Use the Visualize page to filter by repository via the `?repo=` query parameter.
