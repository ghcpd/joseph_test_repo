#!/usr/bin/env python3
"""
integrate_pr_issue.py

Read three JSONL files:
  - sample_data/pr_issue_single_test.jsonl
  - sample_data/pr_detail_test.jsonl
  - sample_data/issue_detail_test.jsonl

Join them using the rules:
  - pr_issue['pull_request']['url'] == pr['url']
  - pr_issue['closing_issue'] == issue['number']

Output is a JSON Lines file at:
  - output_data/merged_data.jsonl

Columns/order (exact):
  ['repo', 'issue_number', 'issue_title', 'issue_body', 'pull_number', 'created_at', 'base_commit_sha', 'merge_commit_sha', 'instance_id', 'pr_url', 'issue_url']

Default behaviour: skip records that do not have both matching PR and Issue. Use --include-missing to include them with missing values filled as null.

Usage example:
  python integrate_pr_issue.py
  python integrate_pr_issue.py --pr-issue-file sample_data/pr_issue_single_test.jsonl --pr-detail-file sample_data/pr_detail_test.jsonl --issue-detail-file sample_data/issue_detail_test.jsonl --output-file output_data/merged_data.jsonl

"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


LOG_FMT = "%(asctime)s %(levelname)s: %(message)s"


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FMT)


def load_pr_details_by_url(pr_detail_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load PR detail JSONL and return a mapping from pr['url'] -> pr_json."""
    logging.info("Loading PR details from %s", pr_detail_path)
    pr_by_url: Dict[str, Dict[str, Any]] = {}

    if not pr_detail_path.exists():
        logging.warning("PR detail file %s does not exist", pr_detail_path)
        return pr_by_url

    with pr_detail_path.open("r", encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                logging.warning("Invalid JSON in PR detail at %s:%d — %s", pr_detail_path, ln, e)
                continue
            url = obj.get("url")
            if url:
                pr_by_url[url] = obj
    logging.info("Loaded %d PR detail records", len(pr_by_url))
    return pr_by_url


def load_issue_details_by_number(issue_detail_path: Path) -> Dict[int, Dict[str, Any]]:
    """Load issue detail JSONL and return a mapping from issue['number'] -> issue_json."""
    logging.info("Loading issue details from %s", issue_detail_path)
    issue_by_number: Dict[int, Dict[str, Any]] = {}

    if not issue_detail_path.exists():
        logging.warning("Issue detail file %s does not exist", issue_detail_path)
        return issue_by_number

    with issue_detail_path.open("r", encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                logging.warning("Invalid JSON in issue detail at %s:%d — %s", issue_detail_path, ln, e)
                continue
            number = obj.get("number")
            if number is not None:
                # Use the integer value as key when possible
                issue_by_number[int(number)] = obj
    logging.info("Loaded %d issue detail records", len(issue_by_number))
    return issue_by_number


def integrate(
    pr_issue_path: Path,
    pr_detail_path: Path,
    issue_detail_path: Path,
    output_path: Path,
    include_missing: bool = False,
) -> int:
    """Integrate the three JSONL files and write merged JSON lines to output_path.

    Returns the number of merged records written.
    """
    pr_by_url = load_pr_details_by_url(pr_detail_path)
    issue_by_number = load_issue_details_by_number(issue_detail_path)

    # Ensure output dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    written = 0
    skipped = 0

    if not pr_issue_path.exists():
        logging.error("PR-Issue file %s does not exist", pr_issue_path)
        return 0

    logging.info("Processing pr_issue lines from %s", pr_issue_path)

    with pr_issue_path.open("r", encoding="utf-8") as fin, output_path.open("w", encoding="utf-8") as fout:
        for ln, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            processed += 1
            try:
                pr_issue = json.loads(line)
            except json.JSONDecodeError as e:
                logging.warning("Invalid JSON in pr_issue file at line %d: %s", ln, e)
                skipped += 1
                continue

            # Get PR URL from the pr_issue entry
            pr_url = None
            pull_request_obj = pr_issue.get("pull_request")
            if isinstance(pull_request_obj, dict):
                pr_url = pull_request_obj.get("url")

            pr_json = pr_by_url.get(pr_url) if pr_url else None

            # Get the closing issue number and find issue detail
            closing_issue = pr_issue.get("closing_issue")
            issue_json = None
            if closing_issue is not None:
                try:
                    issue_num = int(closing_issue)
                except Exception:
                    issue_num = None
                if issue_num is not None:
                    issue_json = issue_by_number.get(issue_num)

            if pr_json is None or issue_json is None:
                if not include_missing:
                    # skip entries that don't have both matches
                    skipped += 1
                    logging.debug(
                        "Skipping pr_issue line %d: pr_url=%s issue=%s (pr found=%s issue found=%s)",
                        ln,
                        pr_url,
                        closing_issue,
                        bool(pr_json),
                        bool(issue_json),
                    )
                    continue
                # else: include but fields can be None

            # Build merged object in exact required order
            repo = pr_issue.get("full_name") or None

            # Pull data from matched PR and issue (if present)
            issue_number = issue_json.get("number") if issue_json else (int(closing_issue) if closing_issue is not None else None)
            issue_title = issue_json.get("title") if issue_json else None
            issue_body = issue_json.get("body") if issue_json else None

            pull_number = pr_json.get("number") if pr_json else None
            created_at = pr_json.get("created_at") if pr_json else None
            base_commit_sha = None
            if pr_json:
                base = pr_json.get("base") or {}
                base_commit_sha = base.get("sha") if isinstance(base, dict) else None
            merge_commit_sha = pr_json.get("merge_commit_sha") if pr_json else None

            instance_id = None
            if repo and pull_number is not None:
                instance_name = repo.replace("/", "__")
                instance_id = f"{instance_name}-{pull_number}"

            pr_url_field = pr_json.get("url") if pr_json else pr_url
            issue_url_field = issue_json.get("url") if issue_json else (f"https://api.github.com/repos/{repo}/issues/{issue_number}" if repo and issue_number is not None else None)

            merged = {
                "repo": repo,
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_body": issue_body,
                "pull_number": pull_number,
                "created_at": created_at,
                "base_commit_sha": base_commit_sha,
                "merge_commit_sha": merge_commit_sha,
                "instance_id": instance_id,
                "pr_url": pr_url_field,
                "issue_url": issue_url_field,
            }

            fout.write(json.dumps(merged, ensure_ascii=False) + "\n")
            written += 1

    logging.info("Done. Processed=%d written=%d skipped=%d", processed, written, skipped)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge PR/issue data into a single JSONL file")

    base_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "--pr-issue-file",
        type=Path,
        default=base_dir / "sample_data" / "pr_issue_single_test.jsonl",
        help="Path to pr_issue JSONL file",
    )
    parser.add_argument(
        "--pr-detail-file",
        type=Path,
        default=base_dir / "sample_data" / "pr_detail_test.jsonl",
        help="Path to PR detail JSONL file",
    )
    parser.add_argument(
        "--issue-detail-file",
        type=Path,
        default=base_dir / "sample_data" / "issue_detail_test.jsonl",
        help="Path to issue detail JSONL file",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=base_dir / "output_data" / "merged_data.jsonl",
        help="Path to output JSONL file (will be created)",
    )
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Include entries with missing PR or issue (fields will be null); default is to skip unmatched entries",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.debug)

    written = integrate(
        pr_issue_path=args.pr_issue_file,
        pr_detail_path=args.pr_detail_file,
        issue_detail_path=args.issue_detail_file,
        output_path=args.output_file,
        include_missing=args.include_missing,
    )

    logging.info("Wrote %d merged lines to %s", written, args.output_file)


if __name__ == "__main__":
    main()
