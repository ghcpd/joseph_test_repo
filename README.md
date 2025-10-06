PR-Issue Dashboard

How to run:
- pip install -r requirements.txt
- python app.py

Endpoints:
- / — dashboard with dataset summary and browsable tables
- /dataset/<dataset>/<id> — record detail with related links
- /visualize — interactive charts, filter by ?repo=owner/repo
- /api/<dataset>?repo=... — raw dataset JSON filtered by repo
- /agg?repo=... — cached aggregated stats for charts

Notes:
- The app loads JSONL files from input_data and output_data.
- Uses Bootstrap + Plotly + DataTables from CDNs.
