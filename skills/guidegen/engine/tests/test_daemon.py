from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

from guidegen_engine.runtime import Session
from guidegen_engine.session.daemon import TOKEN_HEADER, Api, make_handler

from conftest import base_config


def _post(port, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers[TOKEN_HEADER] = token
    req = urllib.request.Request(f"http://127.0.0.1:{port}/", data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_token_required_and_session_persists(ctx, fake):
    api = Api(ctx, Session(base_config(), fake))
    server = HTTPServer(("127.0.0.1", 0), make_handler(api, "tok-123", lambda m: None))
    port = server.server_address[1]
    assert server.server_address[0] == "127.0.0.1"
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        code, body = _post(port, {"method": "ping"})
        assert code == 403 and not body["ok"]
        code, _ = _post(port, {"method": "ping"}, token="wrong")
        assert code == 403
        code, body = _post(port, {"method": "act", "params": {"action": {"action": "click", "target": {"by": "name", "value": "Orders"}}}}, "tok-123")
        assert code == 200 and body["ok"] and body["view"] == "orders"
        code, body = _post(port, {"method": "act", "params": {"action": {"action": "click", "target": {"by": "name", "value": "Delete"}}}}, "tok-123")
        assert body["refused"] is True
        code, body = _post(port, {"method": "tree", "params": {}}, "tok-123")
        assert "New Order" in body["tree"]
        code, body = _post(port, {"method": "shot", "params": {}}, "tok-123")
        assert body["ok"] and (ctx.work / "shots" / "shot-001.png").exists()
        code, body = _post(port, {"method": "shot", "params": {"file": "../../escape.png"}}, "tok-123")
        assert body["ok"] is False
    finally:
        server.shutdown()


def test_tree_output_is_redacted(ctx, fake):
    api = Api(ctx, Session(base_config(), fake))
    assert "support@acme.test" not in api.m_tree()["tree"]
    assert "[redacted]" in api.m_tree()["tree"]
