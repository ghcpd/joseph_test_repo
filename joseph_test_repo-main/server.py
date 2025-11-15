from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import requests
import urllib3
from flask import Flask, jsonify, redirect, request, send_from_directory

app = Flask(__name__, static_folder=".")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_API_URL = "https://api.github.com/repos/{owner}/{repo}"
FETCH_LIMIT = 30
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DISPLAY_DATE_FORMAT = "%Y-%m-%d %H:%M"


@dataclass
class GitHubItem:
    raw: Dict

    def filtered(self) -> Dict:
        labels = [label.get("name", "") for label in self.raw.get("labels", [])]
        data = {
            "number": self.raw.get("number"),
            "title": self.raw.get("title"),
            "author": (self.raw.get("user") or {}).get("login", "Unknown"),
            "status": self._status(),
            "created": self._format_date(self.raw.get("created_at")),
            "updated": self._format_date(self.raw.get("updated_at")),
            "labels": labels,
            "highlight": any(label.lower() == "bug" for label in labels),
            "body": self.raw.get("body", ""),
        }
        return data

    def _status(self) -> str:
        merged_at = self.raw.get("merged_at")
        if merged_at:
            return "merged"
        return self.raw.get("state", "unknown")

    def _format_date(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)
        except (ValueError, TypeError):
            return value


def validate_repo(owner: str, repo: str) -> bool:
    pattern = re.compile(r"^[A-Za-z0-9_.-]+$")
    return bool(pattern.fullmatch(owner) and pattern.fullmatch(repo))


@app.route("/")
def root() -> object:
    return redirect("/index.html")


@app.route("/index.html")
def index() -> object:
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/items")
def fetch_items() -> object:
    owner = request.args.get("owner", "").strip()
    repo = request.args.get("repo", "").strip()
    data_type = request.args.get("type", "pulls").strip().lower()
    if not (owner and repo and validate_repo(owner, repo)):
        return jsonify({"error": "Invalid repository"}), 400

    if data_type not in {"pulls", "issues"}:
        return jsonify({"error": "Invalid type"}), 400

    path = "/pulls" if data_type == "pulls" else "/issues"
    params = {"per_page": FETCH_LIMIT, "state": "all"}
    url = BASE_API_URL.format(owner=owner, repo=repo) + path

    try:
        response = requests.get(
            url,
            params=params,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "GitHub Explorer Demo",
            },
            timeout=10,
            verify=False,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 502

    items = response.json()
    if data_type == "issues":
        items = [item for item in items if "pull_request" not in item]

    normalized = [GitHubItem(item).filtered() for item in items]
    return jsonify({"items": normalized})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)