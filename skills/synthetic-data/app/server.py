"""Review app server for the synthetic-data skill. Python standard library only.

Usage:
    python server.py --data synthetic_data [--port 8765]

Reads and writes, inside the data folder:
    dimensions.json   written by the agent (hypotheses + dimensions)
    tuples.json       written by the agent; the reviewer sets status / edits values
    queries.json      written by the agent; the reviewer marks real / fake / notes
    queries.jsonl     produced by GET /api/export (approved queries only)

The agent may rewrite any of these files at any time; the page polls and reloads.
Reviewer actions are applied per item (by id), so they never overwrite new items
the agent has added.
"""
import argparse
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = threading.Lock()
DATA = "synthetic_data"
FILES = {"dimensions": "dimensions.json", "tuples": "tuples.json", "queries": "queries.json"}
DEFAULTS = {"dimensions": {"product": "", "hypotheses": [], "dimensions": []}, "tuples": [], "queries": []}


def path(kind):
    return os.path.join(DATA, FILES[kind])


def load(kind):
    try:
        with open(path(kind)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULTS[kind]


def save(kind, obj):
    os.makedirs(DATA, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path(kind))


def version():
    v = []
    for k in FILES:
        try:
            v.append(os.stat(path(k)).st_mtime_ns)
        except FileNotFoundError:
            v.append(0)
    return "-".join(map(str, v))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self.send(200, f.read(), "text/html")
        if self.path == "/api/state":
            with LOCK:
                return self.send(200, {"version": version(), **{k: load(k) for k in FILES}})
        if self.path == "/api/version":
            return self.send(200, {"version": version()})
        if self.path == "/api/export":
            with LOCK:
                tuples = {t["id"]: t for t in load("tuples")}
                rows = []
                for q in load("queries"):
                    if q.get("status") == "fake":
                        continue
                    t = tuples.get(q.get("tuple_id"), {})
                    if t.get("status") == "rejected":
                        continue
                    rows.append({"id": q["id"], "tuple": t.get("values", {}), "query": q["query"],
                                 "hypotheses": t.get("hypotheses", []), "review": q.get("status", "unreviewed")})
                os.makedirs(DATA, exist_ok=True)
                out = os.path.join(DATA, "queries.jsonl")
                with open(out, "w") as f:
                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            return self.send(200, {"written": out, "count": len(rows)})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/review":
            return self.send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            kind, item_id = body["kind"], body["id"]
            assert kind in ("tuples", "queries")
        except Exception:
            return self.send(400, {"error": "expected {kind: tuples|queries, id, ...}"})
        with LOCK:
            items = load(kind)
            for it in items:
                if it.get("id") == item_id:
                    for key in ("status", "note"):
                        if key in body:
                            it[key] = body[key]
                    if kind == "tuples" and isinstance(body.get("values"), dict):
                        it.setdefault("values", {}).update(body["values"])
                        it["source"] = "human-edited"
                    if kind == "queries" and isinstance(body.get("query"), str):
                        it["query"] = body["query"]
                        it["source"] = "human-edited"
                    save(kind, items)
                    return self.send(200, {"ok": True, "version": version()})
        self.send(404, {"error": f"no {kind} item with id {item_id}"})


def main():
    global DATA
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="synthetic_data")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    DATA = os.path.abspath(args.data)
    os.makedirs(DATA, exist_ok=True)
    print(f"Synthetic-data review app: http://localhost:{args.port}  (data: {DATA})")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
