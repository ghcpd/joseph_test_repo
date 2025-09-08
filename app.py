import json
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request, url_for, redirect
from urllib.parse import quote, unquote
from collections import defaultdict

BASE_DIR = Path('/home/runner/work/joseph_test_repo/joseph_test_repo')
INPUT_DIR = BASE_DIR / 'input_data'
OUTPUT_DIR = BASE_DIR / 'output_data'

app = Flask(__name__)

# In-memory caches
DATASETS = {}
INDEXES = {}
AGG_CACHE = {}


def load_jsonl(path: Path):
    items = []
    if not path.exists():
        return items
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def build_indexes():
    # pr_issue: use pull_request.url if present else id
    pr_issue = DATASETS['pr_issue']
    idx = {}
    for obj in pr_issue:
        rid = None
        pr = obj.get('pull_request') or {}
        if isinstance(pr, dict) and pr.get('url'):
            rid = pr['url']
        elif 'id' in obj:
            rid = str(obj['id'])
        if rid is not None:
            idx[rid] = obj
    INDEXES['pr_issue'] = idx

    # pr_detail: key by url
    prd = {}
    for obj in DATASETS['pr_detail']:
        rid = obj.get('url') or obj.get('id')
        if rid is not None:
            prd[str(rid)] = obj
    INDEXES['pr_detail'] = prd

    # issue_detail: key by url
    isu = {}
    for obj in DATASETS['issue_detail']:
        rid = obj.get('url') or obj.get('id')
        if rid is not None:
            isu[str(rid)] = obj
    INDEXES['issue_detail'] = isu

    # merged_data: key by instance_id
    md = {}
    for obj in DATASETS['merged_data']:
        rid = obj.get('instance_id')
        if rid is not None:
            md[str(rid)] = obj
    INDEXES['merged_data'] = md


def load_all():
    DATASETS['pr_issue'] = load_jsonl(INPUT_DIR / 'pr_issue_single.jsonl')
    DATASETS['pr_detail'] = load_jsonl(INPUT_DIR / 'pr_detail.jsonl')
    DATASETS['issue_detail'] = load_jsonl(INPUT_DIR / 'issue_detail.jsonl')
    DATASETS['merged_data'] = load_jsonl(OUTPUT_DIR / 'merged_data.jsonl')
    build_indexes()


load_all()


def list_fields(dataset_name):
    if dataset_name == 'merged_data':
        return ['repo', 'issue_number', 'issue_title', 'pull_number', 'created_at']
    # auto-detect top-level keys
    items = DATASETS.get(dataset_name, [])
    if not items:
        return []
    keys = list(items[0].keys())
    # choose a few representative fields
    preferred = ['full_name', 'repo', 'number', 'title', 'created_at', 'id']
    fields = [k for k in preferred if k in keys]
    # fill remaining up to 6
    for k in keys:
        if k not in fields and not isinstance(items[0].get(k), (dict, list)):
            fields.append(k)
        if len(fields) >= 6:
            break
    if not fields:
        fields = [k for k in keys if not isinstance(items[0].get(k), (dict, list))][:6]
    return fields


def record_id_for(dataset, obj):
    if dataset == 'merged_data':
        return obj.get('instance_id')
    if dataset == 'pr_detail':
        return obj.get('url') or str(obj.get('id'))
    if dataset == 'issue_detail':
        return obj.get('url') or str(obj.get('id'))
    if dataset == 'pr_issue':
        pr = obj.get('pull_request') or {}
        return pr.get('url') or str(obj.get('id'))
    return str(id(obj))


@app.route('/')
def home():
    summaries = {name: len(items) for name, items in DATASETS.items()}
    current = request.args.get('dataset', 'merged_data')
    dataset_items = DATASETS.get(current, [])[:500]  # limit for initial table speed
    fields = list_fields(current)
    rows = []
    for it in dataset_items:
        rid = record_id_for(current, it)
        rows.append({'vals': [it.get(k, 'N/A') for k in fields], 'rid': rid})
    return render_template('index.html', summaries=summaries, current=current, fields=fields, rows=rows, record_id_for=record_id_for)


@app.route('/dataset/<dataset>/<path:rid>')
def detail(dataset, rid):
    rid = unquote(rid)
    obj = INDEXES.get(dataset, {}).get(rid)
    if not obj:
        # try alternative: cast to str id
        obj = INDEXES.get(dataset, {}).get(str(rid))
    related = {}
    try:
        if dataset == 'pr_detail':
            # find pr_issue by url
            pi = INDEXES['pr_issue'].get(obj.get('url'))
            if pi and 'closing_issue' in pi:
                issue_num = pi['closing_issue']
                repo = pi.get('full_name')
                # find issue_detail by constructing issue api url
                for v in INDEXES['issue_detail'].values():
                    if v.get('number') == issue_num and repo and repo in v.get('url', ''):
                        related['issue_detail'] = record_id_for('issue_detail', v)
                        break
        elif dataset == 'issue_detail':
            # find related pr via pr_issue
            issue_num = obj.get('number')
            repo_name = (obj.get('repository_url') or '').split('/repos/')[-1]
            for pi in INDEXES['pr_issue'].values():
                if pi.get('closing_issue') == issue_num and pi.get('full_name') == repo_name:
                    prurl = (pi.get('pull_request') or {}).get('url')
                    if prurl and prurl in INDEXES['pr_detail']:
                        related['pr_detail'] = prurl
                        break
        elif dataset == 'merged_data':
            md = obj
            related['pr_detail'] = md.get('pr_url')
            related['issue_detail'] = md.get('issue_url')
    except Exception:
        pass
    return render_template('detail.html', dataset=dataset, obj=obj, related=related, record_id_for=record_id_for)


@app.route('/api/<dataset_name>')
def api_dataset(dataset_name):
    repo_filter = request.args.get('repo')
    items = DATASETS.get(dataset_name, [])
    if repo_filter:
        rf = repo_filter.lower()
        def match_repo(o):
            # try various fields
            return (str(o.get('repo') or '').lower().startswith(rf) or
                    str(o.get('full_name') or '').lower().startswith(rf) or
                    rf in str(o.get('repository_url') or '').lower())
        items = [o for o in items if match_repo(o)]
    return jsonify(items)


@app.route('/visualize')
def visualize():
    repo = request.args.get('repo')
    return render_template('visualize.html', repo=repo)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=False)