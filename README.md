# SQLite Tracker Project

This project manages Pull Requests (PRs) and Issues data in an SQLite database.

## Project Structure

```
project/
├── database/
│   └── tracker.db          # SQLite database file
├── input_data/
│   ├── pr_detail.jsonl      # PR data in JSONL format
│   └── issue_detail.jsonl   # Issue data in JSONL format
└── scripts/
    ├── init_db.py           # Initialize database tables
    ├── load_data.py         # Load data from JSONL files
    ├── show_table.py        # Display table contents
    └── aggregate_stats.py   # Show aggregate statistics
```

## Usage Examples

### 1. Initialize the Database
```bash
python scripts/init_db.py
```
- Creates the SQLite database with `pr` and `issue` tables
- Safe to run multiple times (won't recreate existing tables)
- Includes unique constraints to prevent duplicate entries

### 2. Load Data from JSONL Files
```bash
python scripts/load_data.py
```
- Loads PR and Issue data from the `input_data/` directory
- Safe to run multiple times (prevents duplicate insertions)
- Reports how many new records were inserted

### 3. Display Table Contents
```bash
python scripts/show_table.py <table_name>
```

Examples:
```bash
python scripts/show_table.py pr       # Show all PRs
python scripts/show_table.py issue    # Show all Issues
```

### 4. View Aggregate Statistics
```bash
python scripts/aggregate_stats.py
```
- Shows count of PRs and Issues per repository
- Analyzes PR bodies to find "Fixes #<issue_number>" patterns
- Displays statistics on how many issues each PR fixes

## Complete Setup and Usage Example

```bash
# 1. Initialize the database
python scripts/init_db.py

# 2. Load the data
python scripts/load_data.py

# 3. View the data
python scripts/show_table.py pr
python scripts/show_table.py issue

# 4. See statistics
python scripts/aggregate_stats.py

# 5. Running again is safe (no duplicates)
python scripts/load_data.py  # Will show "Inserted 0 new PRs and 0 new issues"
```

## Features

### Bug Fixes Applied
- ✅ **Fixed duplicate insertion bug**: `load_data.py` now uses `INSERT OR IGNORE` with unique constraints
- ✅ **Safe multiple runs**: All scripts can be run multiple times without issues
- ✅ **Better reporting**: Scripts now report what was actually inserted/updated

### New Features Added
- ✅ **Table viewer**: `show_table.py` displays any table in a formatted layout
- ✅ **Statistics engine**: `aggregate_stats.py` provides comprehensive analytics
- ✅ **PR-Issue linking**: Parses "Fixes #<number>" patterns from PR bodies
- ✅ **Error handling**: All scripts include proper error handling and validation

### Technical Implementation
- Uses only Python standard library (sqlite3, os, sys, json, re)
- Unique constraints on (repo_name, pr_number) and (repo_name, issue_number)
- Comprehensive error handling and user-friendly messages
- Clean, readable, and well-commented code
- Proper input validation and edge case handling

## Database Schema

### PR Table
```sql
CREATE TABLE pr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    title TEXT,
    body TEXT,
    UNIQUE(repo_name, pr_number)
);
```

### Issue Table
```sql
CREATE TABLE issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    issue_number INTEGER NOT NULL,
    title TEXT,
    body TEXT,
    UNIQUE(repo_name, issue_number)
);
```