#!/usr/bin/env python3
"""
Script to display the contents of any table in the SQLite database.
Usage: python scripts/show_table.py <table_name>
"""

import sqlite3
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")

def show_table(table_name):
    """Display all rows from the specified table in a readable format."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run 'python scripts/init_db.py' first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Get table schema to display column names
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        
        if not columns:
            print(f"Error: Table '{table_name}' does not exist.")
            print("Available tables:")
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = c.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
            return
        
        # Get column names
        column_names = [col[1] for col in columns]
        
        # Get all rows from the table
        c.execute(f"SELECT * FROM {table_name}")
        rows = c.fetchall()
        
        # Display results
        print(f"\nTable: {table_name}")
        print("=" * 50)
        
        if not rows:
            print("No data found in this table.")
        else:
            # Calculate column widths for better formatting
            widths = []
            for i, col_name in enumerate(column_names):
                max_width = len(col_name)
                for row in rows:
                    if row[i] is not None:
                        max_width = max(max_width, len(str(row[i])))
                widths.append(min(max_width, 50))  # Limit column width to 50 chars
            
            # Print header
            header = " | ".join(col_name.ljust(widths[i]) for i, col_name in enumerate(column_names))
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in rows:
                formatted_row = []
                for i, value in enumerate(row):
                    if value is None:
                        formatted_value = "NULL"
                    else:
                        str_value = str(value)
                        # Truncate long values and add ellipsis
                        if len(str_value) > widths[i]:
                            formatted_value = str_value[:widths[i]-3] + "..."
                        else:
                            formatted_value = str_value
                    formatted_row.append(formatted_value.ljust(widths[i]))
                print(" | ".join(formatted_row))
        
        print(f"\nTotal rows: {len(rows)}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/show_table.py <table_name>")
        print("Example: python scripts/show_table.py pr")
        sys.exit(1)
    
    table_name = sys.argv[1]
    show_table(table_name)

if __name__ == "__main__":
    main()