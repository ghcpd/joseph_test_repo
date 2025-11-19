#!/usr/bin/env python
"""
integrate_pr_issue.py - Reference script for merging PR and issue data

This script demonstrates how the merged_data.jsonl file is created by combining
data from pr_issue_single.jsonl, pr_detail.jsonl, and issue_detail.jsonl.

The integration logic:
1. Reads pr_issue_single.jsonl which contains PR info with closing_issue references
2. Reads pr_detail.jsonl for detailed PR information
3. Reads issue_detail.jsonl for detailed issue information
4. Matches PRs to issues using repo and issue/PR numbers
5. Outputs merged_data.jsonl with combined information

Example merged record structure:
{
    "repo": "owner/repo1",
    "issue_number": 1,
    "issue_title": "Login page not loading",
    "pull_number": 101,
    "pr_title": "Fix login bug",
    "created_at": "2024-01-15T10:30:00Z",
    "merged_at": "2024-01-16T12:00:00Z",
    "issue_created_at": "2024-01-10T08:00:00Z"
}

Usage:
    python integrate_pr_issue.py

This will read from input_data/ and write to output_data/merged_data.jsonl
"""

import json
import os


def load_jsonl(filepath):
    """Load a JSONL file and return list of dictionaries."""
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return data


def integrate_pr_issue():
    """Integrate PR and issue data into merged format."""
    # Load input files
    pr_issue_data = load_jsonl('input_data/pr_issue_single.jsonl')
    pr_detail_data = load_jsonl('input_data/pr_detail.jsonl')
    issue_detail_data = load_jsonl('input_data/issue_detail.jsonl')
    
    # Create lookup dictionaries
    pr_lookup = {(pr['repo'], pr['pr_number']): pr for pr in pr_detail_data}
    issue_lookup = {(issue['repo'], issue['issue_number']): issue for issue in issue_detail_data}
    
    # Merge data
    merged = []
    for pr_issue in pr_issue_data:
        repo = pr_issue['repo']
        pr_number = pr_issue['pr_number']
        
        # Get detailed PR info
        pr_detail = pr_lookup.get((repo, pr_number))
        if not pr_detail:
            continue
            
        # Try to find matching issue
        # In this example, we use a simplified approach
        # In reality, you'd need to parse closing_issue or use GitHub API
        issue_number = pr_issue.get('closing_issue')
        if not issue_number:
            continue
            
        issue_detail = issue_lookup.get((repo, issue_number))
        if not issue_detail:
            continue
        
        # Create merged record
        merged_record = {
            'repo': repo,
            'issue_number': issue_number,
            'issue_title': issue_detail['title'],
            'pull_number': pr_number,
            'pr_title': pr_detail['title'],
            'created_at': pr_detail['created_at'],
            'merged_at': pr_detail.get('merged_at'),
            'issue_created_at': issue_detail['created_at']
        }
        merged.append(merged_record)
    
    # Write output
    os.makedirs('output_data', exist_ok=True)
    with open('output_data/merged_data.jsonl', 'w') as f:
        for record in merged:
            f.write(json.dumps(record) + '\n')
    
    print(f"Created merged_data.jsonl with {len(merged)} records")


if __name__ == '__main__':
    integrate_pr_issue()
