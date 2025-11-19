import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Global data storage
datasets = {
    'pr_issue_single': [],
    'pr_detail': [],
    'issue_detail': [],
    'merged_data': []
}

# Cached aggregations for performance
cache = {}


def load_jsonl(filepath):
    """Load JSONL file and return list of dictionaries."""
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return data


def load_all_data():
    """Load all JSONL files into memory at startup."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    datasets['pr_issue_single'] = load_jsonl(os.path.join(base_path, 'input_data/pr_issue_single.jsonl'))
    datasets['pr_detail'] = load_jsonl(os.path.join(base_path, 'input_data/pr_detail.jsonl'))
    datasets['issue_detail'] = load_jsonl(os.path.join(base_path, 'input_data/issue_detail.jsonl'))
    datasets['merged_data'] = load_jsonl(os.path.join(base_path, 'output_data/merged_data.jsonl'))
    
    print(f"Loaded {len(datasets['pr_issue_single'])} records from pr_issue_single")
    print(f"Loaded {len(datasets['pr_detail'])} records from pr_detail")
    print(f"Loaded {len(datasets['issue_detail'])} records from issue_detail")
    print(f"Loaded {len(datasets['merged_data'])} records from merged_data")


def get_record_by_id(dataset_name, record_id):
    """Get a specific record from a dataset by ID."""
    data = datasets.get(dataset_name, [])
    
    # Try different ID fields
    for record in data:
        if str(record.get('id')) == str(record_id):
            return record
        if str(record.get('pr_number')) == str(record_id):
            return record
        if str(record.get('issue_number')) == str(record_id):
            return record
    
    # For merged_data, use index
    if dataset_name == 'merged_data':
        try:
            idx = int(record_id)
            if 0 <= idx < len(data):
                return data[idx]
        except (ValueError, IndexError):
            pass
    
    return None


def find_related_data(dataset_name, record):
    """Find related data across datasets."""
    related = {}
    
    if dataset_name == 'pr_detail':
        pr_number = record.get('pr_number')
        repo = record.get('repo')
        
        # Find matching issue in merged_data
        for merged in datasets['merged_data']:
            if merged.get('pull_number') == pr_number and merged.get('repo') == repo:
                issue_num = merged.get('issue_number')
                for issue in datasets['issue_detail']:
                    if issue.get('issue_number') == issue_num and issue.get('repo') == repo:
                        related['issue'] = issue
                        break
                break
    
    elif dataset_name == 'issue_detail':
        issue_number = record.get('issue_number')
        repo = record.get('repo')
        
        # Find matching PR in merged_data
        for merged in datasets['merged_data']:
            if merged.get('issue_number') == issue_number and merged.get('repo') == repo:
                pr_num = merged.get('pull_number')
                for pr in datasets['pr_detail']:
                    if pr.get('pr_number') == pr_num and pr.get('repo') == repo:
                        related['pr'] = pr
                        break
                break
    
    elif dataset_name == 'merged_data':
        repo = record.get('repo')
        issue_num = record.get('issue_number')
        pr_num = record.get('pull_number')
        
        # Find source issue and PR
        for issue in datasets['issue_detail']:
            if issue.get('issue_number') == issue_num and issue.get('repo') == repo:
                related['issue'] = issue
                break
        
        for pr in datasets['pr_detail']:
            if pr.get('pr_number') == pr_num and pr.get('repo') == repo:
                related['pr'] = pr
                break
    
    return related


def compute_visualizations(repo_filter=None):
    """Compute aggregations for visualizations with optional repo filter."""
    cache_key = f"viz_{repo_filter or 'all'}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    viz_data = {}
    
    # Filter datasets by repo if specified
    def filter_by_repo(data):
        if repo_filter:
            return [r for r in data if r.get('repo') == repo_filter]
        return data
    
    # Merged data visualizations
    merged = filter_by_repo(datasets['merged_data'])
    
    # Top 10 repos by PR count
    repo_counts = Counter([r['repo'] for r in merged])
    viz_data['top_repos'] = dict(repo_counts.most_common(10))
    
    # Time series of PR creation dates
    date_counts = defaultdict(int)
    for record in merged:
        created_at = record.get('created_at', '')
        if created_at:
            date = created_at.split('T')[0][:7]  # YYYY-MM
            date_counts[date] += 1
    viz_data['pr_timeline'] = dict(sorted(date_counts.items()))
    
    # PR issue single visualizations
    pr_issue = filter_by_repo(datasets['pr_issue_single'])
    closing_issue_counts = defaultdict(int)
    for record in pr_issue:
        repo = record.get('repo')
        closing_issue_counts[repo] += record.get('closing_issue', 0)
    viz_data['closing_issue_dist'] = dict(closing_issue_counts)
    
    # PR detail visualizations
    pr_detail = filter_by_repo(datasets['pr_detail'])
    month_counts = defaultdict(int)
    for record in pr_detail:
        created_at = record.get('created_at', '')
        if created_at:
            month = created_at.split('T')[0][:7]  # YYYY-MM
            month_counts[month] += 1
    viz_data['pr_by_month'] = dict(sorted(month_counts.items()))
    
    # Issue detail visualizations
    issue_detail = filter_by_repo(datasets['issue_detail'])
    label_counts = Counter()
    for record in issue_detail:
        labels = record.get('labels', [])
        if isinstance(labels, list):
            label_counts.update(labels)
    viz_data['top_labels'] = dict(label_counts.most_common(10))
    
    cache[cache_key] = viz_data
    return viz_data


@app.route('/')
def index():
    """Homepage with dashboard and dataset switcher."""
    selected_dataset = request.args.get('dataset', 'merged_data')
    
    # Summary statistics
    summary = {
        'pr_issue_single': len(datasets['pr_issue_single']),
        'pr_detail': len(datasets['pr_detail']),
        'issue_detail': len(datasets['issue_detail']),
        'merged_data': len(datasets['merged_data'])
    }
    
    # Get data for selected dataset
    data = datasets.get(selected_dataset, [])
    
    # Get column names dynamically
    columns = []
    if data:
        columns = list(data[0].keys())
    
    return render_template('index.html', 
                         summary=summary,
                         selected_dataset=selected_dataset,
                         data=data,
                         columns=columns)


@app.route('/dataset/<dataset_name>/<record_id>')
def dataset_detail(dataset_name, record_id):
    """Show detail page for a specific record."""
    if dataset_name not in datasets:
        return "Dataset not found", 404
    
    record = get_record_by_id(dataset_name, record_id)
    if not record:
        return "Record not found", 404
    
    related = find_related_data(dataset_name, record)
    
    return render_template('detail.html',
                         dataset_name=dataset_name,
                         record=record,
                         related=related)


@app.route('/visualize')
def visualize():
    """Visualization page with interactive charts."""
    repo_filter = request.args.get('repo')
    
    viz_data = compute_visualizations(repo_filter)
    
    # Get list of all repos for filter dropdown
    all_repos = set()
    for dataset in datasets.values():
        for record in dataset:
            if 'repo' in record:
                all_repos.add(record['repo'])
    
    return render_template('visualize.html',
                         viz_data=viz_data,
                         repos=sorted(all_repos),
                         selected_repo=repo_filter)


@app.route('/api/<dataset_name>')
def api_dataset(dataset_name):
    """JSON API endpoint for dataset data."""
    if dataset_name not in datasets:
        return jsonify({'error': 'Dataset not found'}), 404
    
    repo_filter = request.args.get('repo')
    data = datasets[dataset_name]
    
    if repo_filter:
        data = [r for r in data if r.get('repo') == repo_filter]
    
    return jsonify({
        'dataset': dataset_name,
        'count': len(data),
        'data': data
    })


@app.template_filter('format_date')
def format_date(value):
    """Format ISO date string to readable format."""
    if not value or value == 'N/A':
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return value


@app.template_filter('format_value')
def format_value(value):
    """Format value for display, handling None and complex types."""
    if value is None:
        return 'N/A'
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


if __name__ == '__main__':
    load_all_data()
    # Use DEBUG environment variable to enable debug mode (default: False)
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
