#!/usr/bin/env python3
"""Run an Apify actor and save its dataset as JSON.

Usage: python3 scripts/apify_run.py <actor_id> <input.json> <out.json>

The token is read from the APIFY_API_KEY environment variable (or a .env file
in the current directory). It is never printed.
"""
import json, os, sys, time, urllib.request
from pathlib import Path


def load_token():
    token = os.environ.get("APIFY_API_KEY")
    env = Path(".env")
    if not token and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("APIFY_API_KEY="):
                token = line.split("=", 1)[1].strip().strip('"')
    if not token:
        sys.exit("APIFY_API_KEY is not set. Export it or put it in .env (never commit it).")
    return token


TOKEN = load_token()


def call(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


if len(sys.argv) != 4:
    sys.exit(__doc__)
actor, inp, out = sys.argv[1].replace("/", "~"), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
run = call(f"https://api.apify.com/v2/acts/{actor}/runs", inp)["data"]
print("run", run["id"], flush=True)
while run["status"] in ("READY", "RUNNING"):
    time.sleep(10)
    run = call(f"https://api.apify.com/v2/actor-runs/{run['id']}")["data"]
items = call(f"https://api.apify.com/v2/datasets/{run['defaultDatasetId']}/items?clean=true&format=json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(items, ensure_ascii=False, indent=1))
print(run["status"], len(items), "items ->", out, "cost $", run.get("usageTotalUsd"))
