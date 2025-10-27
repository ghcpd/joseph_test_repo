#!/usr/bin/env python3
"""
Flask web application to process and visualize PR/Issue data.

Loads four JSONL files and provides web interface for browsing and visualizing the data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime
import re

from flask import Flask, render_template, request, jsonify, abort, url_for

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global data storage
data_store = {
    'pr_issue_single': {},
    'pr_detail': {},
    'issue_detail': {},
    'merged_data': {}
}

# Indexes for quick lookup
indexes = {
    'pr_detail_by_url': {},
    'issue_detail_by_number': {},
    'merged_data_by_id': {}
}

def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of records."""
    records = []
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist")
        return records
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON at {file_path}:{line_num} - {e}")
    
    logger.info(f"Loaded {len(records)} records from {file_path}")
    return records

def load_all_data():
    """Load all JSONL files into memory and create indexes."""
    base_path = Path(__file__).parent
    
    # Load data files
    datasets = {
        'pr_issue_single': base_path / 'input_data' / 'pr_issue_single.jsonl',
        'pr_detail': base_path / 'input_data' / 'pr_detail.jsonl', 
        'issue_detail': base_path / 'input_data' / 'issue_detail.jsonl',
        'merged_data': base_path / 'output_data' / 'merged_data.jsonl'
    }
    
    for dataset_name, file_path in datasets.items():
        records = load_jsonl_file(file_path)
        
        # Store records with numeric index
        for i, record in enumerate(records):
            data_store[dataset_name][i] = record
    
    # Create lookup indexes
    for i, record in data_store['pr_detail'].items():
        if 'url' in record:
            indexes['pr_detail_by_url'][record['url']] = i
    
    for i, record in data_store['issue_detail'].items():
        if 'number' in record:
            indexes['issue_detail_by_number'][record['number']] = i
    
    for i, record in data_store['merged_data'].items():
        if 'instance_id' in record:
            indexes['merged_data_by_id'][record['instance_id']] = i

def get_dataset_summary():
    """Get summary statistics for all datasets."""
    summary = {}
    for dataset_name, records in data_store.items():
        summary[dataset_name] = {
            'count': len(records),
            'sample_keys': list(records[0].keys()) if records else []
        }
    return summary

def get_table_columns(dataset_name: str) -> List[str]:
    """Get appropriate columns for table display."""
    if dataset_name == 'merged_data':
        return ['repo', 'issue_number', 'issue_title', 'pull_number', 'created_at']
    elif dataset_name == 'pr_issue_single':
        return ['number', 'title', 'state', 'created_at', 'full_name', 'closing_issue']
    elif dataset_name == 'pr_detail':
        return ['number', 'title', 'state', 'created_at', 'user']
    elif dataset_name == 'issue_detail':
        return ['number', 'title', 'state', 'created_at', 'user']
    return []

def safe_get(record: Dict, key: str) -> str:
    """Safely get value from record, handling nested objects."""
    value = record.get(key)
    if value is None:
        return "N/A"
    if isinstance(value, dict):
        # For user objects, return login
        if key == 'user' and 'login' in value:
            return value['login']
        return str(value)
    return str(value)

def find_related_data(dataset_name: str, record_id: int) -> Dict[str, List]:
    """Find related records across datasets."""
    related = {'pr_detail': [], 'issue_detail': [], 'merged_data': []}
    
    if dataset_name not in data_store or record_id not in data_store[dataset_name]:
        return related
    
    record = data_store[dataset_name][record_id]
    
    if dataset_name == 'pr_detail':
        # Find related issue via pr_issue_single
        pr_url = record.get('url')
        if pr_url:
            for pr_issue_record in data_store['pr_issue_single'].values():
                if (pr_issue_record.get('pull_request', {}).get('url') == pr_url and 
                    'closing_issue' in pr_issue_record):
                    issue_num = pr_issue_record['closing_issue']
                    if issue_num in indexes['issue_detail_by_number']:
                        issue_id = indexes['issue_detail_by_number'][issue_num]
                        related['issue_detail'].append(issue_id)
    
    elif dataset_name == 'issue_detail':
        # Find related PR via pr_issue_single  
        issue_num = record.get('number')
        if issue_num:
            for pr_issue_record in data_store['pr_issue_single'].values():
                if pr_issue_record.get('closing_issue') == issue_num:
                    pr_url = pr_issue_record.get('pull_request', {}).get('url')
                    if pr_url and pr_url in indexes['pr_detail_by_url']:
                        pr_id = indexes['pr_detail_by_url'][pr_url]
                        related['pr_detail'].append(pr_id)
    
    elif dataset_name == 'merged_data':
        # Find source records
        repo = record.get('repo')
        issue_num = record.get('issue_number')
        pull_num = record.get('pull_number')
        
        if issue_num and issue_num in indexes['issue_detail_by_number']:
            related['issue_detail'].append(indexes['issue_detail_by_number'][issue_num])
        
        # Find PR by looking for matching number and checking repo
        if pull_num and repo:
            for pr_id, pr_record in data_store['pr_detail'].items():
                if (pr_record.get('number') == pull_num and 
                    pr_record.get('url', '').find(repo.replace('/', '/repos/')) > -1):
                    related['pr_detail'].append(pr_id)
                    break
    
    return related

@app.route('/')
def homepage():
    """Homepage with dashboard and dataset browser."""
    dataset = request.args.get('dataset', 'merged_data')
    if dataset not in data_store:
        dataset = 'merged_data'
    
    summary = get_dataset_summary()
    columns = get_table_columns(dataset)
    
    # Get sample records for table
    records = []
    for record_id, record in list(data_store[dataset].items())[:100]:  # Limit to 100 for performance
        row = {'id': record_id}
        for col in columns:
            row[col] = safe_get(record, col)
        records.append(row)
    
    return render_template('homepage.html', 
                         summary=summary,
                         current_dataset=dataset,
                         columns=columns,
                         records=records,
                         dataset_names=list(data_store.keys()))

@app.route('/dataset/<dataset_name>/<int:record_id>')
def dataset_detail(dataset_name: str, record_id: int):
    """Show detailed view of a single record."""
    if dataset_name not in data_store or record_id not in data_store[dataset_name]:
        abort(404)
    
    record = data_store[dataset_name][record_id]
    related = find_related_data(dataset_name, record_id)
    
    return render_template('detail.html',
                         dataset_name=dataset_name,
                         record_id=record_id,
                         record=record,
                         related=related)

@app.route('/visualize')
def visualize():
    """Visualization page with interactive charts."""
    repo_filter = request.args.get('repo', '')
    return render_template('visualize.html', repo_filter=repo_filter)

@app.route('/api/<dataset_name>')
def api_dataset(dataset_name: str):
    """JSON API endpoint for dataset data."""
    if dataset_name not in data_store:
        abort(404)
    
    repo_filter = request.args.get('repo', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    records = []
    for record_id, record in data_store[dataset_name].items():
        # Apply repo filter if specified
        if repo_filter:
            record_repo = record.get('repo') or record.get('full_name', '')
            if repo_filter.lower() not in record_repo.lower():
                continue
        
        record_copy = dict(record)
        record_copy['_id'] = record_id
        records.append(record_copy)
    
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = records[start:end]
    
    return jsonify({
        'data': paginated_records,
        'total': len(records),
        'page': page,
        'per_page': per_page,
        'pages': (len(records) + per_page - 1) // per_page
    })

@app.route('/api/chart_data/<chart_type>')
def api_chart_data(chart_type: str):
    """API endpoint for chart data."""
    repo_filter = request.args.get('repo', '')
    
    if chart_type == 'top_repos':
        # Top 10 repos by PR count from merged_data
        repo_counts = Counter()
        for record in data_store['merged_data'].values():
            repo = record.get('repo')
            if repo and (not repo_filter or repo_filter.lower() in repo.lower()):
                repo_counts[repo] += 1
        
        top_repos = repo_counts.most_common(10)
        return jsonify({
            'labels': [repo for repo, count in top_repos],
            'data': [count for repo, count in top_repos]
        })
    
    elif chart_type == 'pr_timeline':
        # PR creation timeline from merged_data
        date_counts = defaultdict(int)
        for record in data_store['merged_data'].values():
            repo = record.get('repo', '')
            if repo_filter and repo_filter.lower() not in repo.lower():
                continue
                
            created_at = record.get('created_at')
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    date_counts[month_key] += 1
                except:
                    pass
        
        sorted_dates = sorted(date_counts.items())
        return jsonify({
            'labels': [date for date, count in sorted_dates],
            'data': [count for date, count in sorted_dates]
        })
    
    elif chart_type == 'closing_issue_distribution':
        # Distribution of closing_issue counts per repo from pr_issue_single
        repo_closing_counts = defaultdict(int)
        for record in data_store['pr_issue_single'].values():
            repo = record.get('full_name')
            if repo and record.get('closing_issue') and (not repo_filter or repo_filter.lower() in repo.lower()):
                repo_closing_counts[repo] += 1
        
        top_repos = sorted(repo_closing_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return jsonify({
            'labels': [repo for repo, count in top_repos],
            'data': [count for repo, count in top_repos]
        })
    
    elif chart_type == 'pr_monthly':
        # PR histogram by month/year from pr_detail
        date_counts = defaultdict(int)
        for record in data_store['pr_detail'].values():
            # Extract repo from URL for filtering
            url = record.get('url', '')
            if repo_filter:
                if repo_filter.lower() not in url.lower():
                    continue
            
            created_at = record.get('created_at')
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    date_counts[month_key] += 1
                except:
                    pass
        
        sorted_dates = sorted(date_counts.items())
        return jsonify({
            'labels': [date for date, count in sorted_dates],
            'data': [count for date, count in sorted_dates]
        })
    
    elif chart_type == 'top_labels':
        # Top 10 labels used across issues from issue_detail
        label_counts = Counter()
        for record in data_store['issue_detail'].values():
            # Extract repo from URL for filtering
            url = record.get('url', '')
            if repo_filter:
                if repo_filter.lower() not in url.lower():
                    continue
            
            labels = record.get('labels', [])
            if isinstance(labels, list):
                for label in labels:
                    if isinstance(label, dict) and 'name' in label:
                        label_counts[label['name']] += 1
        
        top_labels = label_counts.most_common(10)
        return jsonify({
            'labels': [label for label, count in top_labels],
            'data': [count for label, count in top_labels]
        })
    
    abort(404)

if __name__ == '__main__':
    logger.info("Loading data...")
    load_all_data()
    logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)