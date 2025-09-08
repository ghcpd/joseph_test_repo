#!/usr/bin/env python3
"""
Script to display aggregate statistics for PRs and Issues.
- Counts the number of PRs and Issues per repository
- Counts how many Issues each PR fixes (based on "Fixes #<issue_number>" in PR body)
- Displays results in formatted tables
"""

import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")

def get_repo_stats():
    """Get count of PRs and Issues per repository."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get PR counts per repo
    c.execute('''
        SELECT repo_name, COUNT(*) as pr_count
        FROM pr 
        GROUP BY repo_name
        ORDER BY repo_name
    ''')
    pr_counts = dict(c.fetchall())
    
    # Get Issue counts per repo
    c.execute('''
        SELECT repo_name, COUNT(*) as issue_count
        FROM issue 
        GROUP BY repo_name
        ORDER BY repo_name
    ''')
    issue_counts = dict(c.fetchall())
    
    conn.close()
    
    # Combine results
    all_repos = set(pr_counts.keys()) | set(issue_counts.keys())
    repo_stats = []
    
    for repo in sorted(all_repos):
        repo_stats.append({
            'repo_name': repo,
            'pr_count': pr_counts.get(repo, 0),
            'issue_count': issue_counts.get(repo, 0)
        })
    
    return repo_stats

def parse_fixes_from_body(body):
    """Extract issue numbers that are fixed from PR body using regex."""
    if not body:
        return []
    
    # Pattern to match "Fixes #<number>" (case insensitive)
    pattern = r'\bfixes?\s+#(\d+)\b'
    matches = re.findall(pattern, body, re.IGNORECASE)
    return [int(match) for match in matches]

def get_pr_fixes_stats():
    """Get statistics on how many issues each PR fixes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all PRs with their bodies
    c.execute('SELECT repo_name, pr_number, title, body FROM pr ORDER BY repo_name, pr_number')
    prs = c.fetchall()
    
    pr_fixes = []
    total_fixes = 0
    
    for repo_name, pr_number, title, body in prs:
        fixed_issues = parse_fixes_from_body(body)
        total_fixes += len(fixed_issues)
        
        pr_fixes.append({
            'repo_name': repo_name,
            'pr_number': pr_number,
            'title': title,
            'fixes_count': len(fixed_issues),
            'fixed_issues': fixed_issues
        })
    
    conn.close()
    return pr_fixes, total_fixes

def print_repo_stats(repo_stats):
    """Print repository statistics in a formatted table."""
    print("\n" + "="*60)
    print("REPOSITORY STATISTICS")
    print("="*60)
    
    print(f"{'Repository':<20} {'PRs':<10} {'Issues':<10} {'Total':<10}")
    print("-" * 60)
    
    total_prs = 0
    total_issues = 0
    
    for stat in repo_stats:
        repo = stat['repo_name']
        pr_count = stat['pr_count']
        issue_count = stat['issue_count']
        total = pr_count + issue_count
        
        print(f"{repo:<20} {pr_count:<10} {issue_count:<10} {total:<10}")
        total_prs += pr_count
        total_issues += issue_count
    
    print("-" * 60)
    print(f"{'TOTAL':<20} {total_prs:<10} {total_issues:<10} {total_prs + total_issues:<10}")

def print_pr_fixes_stats(pr_fixes, total_fixes):
    """Print PR fixes statistics in a formatted table."""
    print("\n" + "="*80)
    print("PR FIXES STATISTICS")
    print("="*80)
    
    print(f"{'Repository':<12} {'PR #':<6} {'Fixes':<7} {'Title':<25} {'Fixed Issues':<20}")
    print("-" * 80)
    
    prs_with_fixes = 0
    
    for pr in pr_fixes:
        repo = pr['repo_name']
        pr_num = pr['pr_number']
        fixes_count = pr['fixes_count']
        title = pr['title'][:24] + "..." if len(pr['title']) > 24 else pr['title']
        fixed_issues = ", ".join([f"#{issue}" for issue in pr['fixed_issues']])
        
        if fixes_count > 0:
            prs_with_fixes += 1
            print(f"{repo:<12} {pr_num:<6} {fixes_count:<7} {title:<25} {fixed_issues:<20}")
    
    if prs_with_fixes == 0:
        print("No PRs found that fix issues (using 'Fixes #<number>' pattern)")
    
    print("-" * 80)
    print(f"Total PRs: {len(pr_fixes)}")
    print(f"PRs that fix issues: {prs_with_fixes}")
    print(f"Total issues fixed: {total_fixes}")
    
    if len(pr_fixes) > 0:
        print(f"Average issues fixed per PR: {total_fixes / len(pr_fixes):.2f}")

def validate_database():
    """Check if database exists and has data."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run 'python scripts/init_db.py' and 'python scripts/load_data.py' first.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("SELECT COUNT(*) FROM pr")
        pr_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM issue")
        issue_count = c.fetchone()[0]
        
        if pr_count == 0 and issue_count == 0:
            print("Warning: Database is empty. Please run 'python scripts/load_data.py' to load data.")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()
    
    return True

def main():
    """Main function to run aggregate statistics."""
    print("Aggregate Statistics Report")
    print("Generated for SQLite Tracker Database")
    
    if not validate_database():
        return
    
    # Get and display repository statistics
    repo_stats = get_repo_stats()
    print_repo_stats(repo_stats)
    
    # Get and display PR fixes statistics
    pr_fixes, total_fixes = get_pr_fixes_stats()
    print_pr_fixes_stats(pr_fixes, total_fixes)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()