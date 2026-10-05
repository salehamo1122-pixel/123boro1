from flask import Flask, jsonify, request
from threading import Thread
import os, hmac, hashlib, json, time, urllib.parse

app = Flask(__name__)
PROCESS_STARTED_AT = time.time()


def _valid(init_data):
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or not init_data:
        return False, {}
    try:
        d = dict(urllib.parse.parse_qsl(init_data, strict_parsing=True))
        received = d.pop("hash", None)
        if not received: return False, {}
        auth_date = int(d.get("auth_date", "0"))
        if abs(time.time() - auth_date) > 86400: return False, {}
        check = "\n".join(f"{k}={d[k]}" for k in sorted(d))
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received): return False, {}
        return True, json.loads(d.get("user", "{}"))
    except Exception:
        return False, {}


def _admin_ok():
    ok, user = _valid(request.headers.get("X-Telegram-Init-Data", ""))
    try: admin = int(os.getenv("ADMIN_USER_ID", "0"))
    except Exception: admin = 0
    return ok and admin > 0 and int(user.get("id", 0)) == admin


@app.route("/")
def home(): return "Salself is alive", 200

@app.route("/health")
def health(): return jsonify(ok=True, service="salself")

@app.route("/miniapp")
def miniapp():
    import miniapp as ma
    return ma.PAGE, 200, {"Content-Type":"text/html; charset=utf-8", "Cache-Control":"no-store, no-cache, must-revalidate"}

@app.get("/api/miniapp/state")
def miniapp_state():
    if not _admin_ok(): return jsonify(ok=False,error="Unauthorized"), 403
    import miniapp as ma
    return jsonify(ok=True, **ma.state())

@app.post("/api/miniapp/toggle")
def miniapp_toggle():
    if not _admin_ok(): return jsonify(ok=False,error="Unauthorized"), 403
    import miniapp as ma
    body=request.get_json(silent=True) or {}
    try: res=ma.toggle(str(body.get("id","")), bool(body.get("enabled")))
    except Exception as e: return jsonify(ok=False,error=str(e)[:160]),500
    if res is None: return jsonify(ok=False,error="Unknown feature"),404
    return jsonify(ok=True,enabled=res)

@app.post("/api/miniapp/master")
def miniapp_master():
    if not _admin_ok(): return jsonify(ok=False,error="Unauthorized"),403
    import miniapp as ma
    body=request.get_json(silent=True) or {}
    return jsonify(ok=True,enabled=ma.set_master(bool(body.get("enabled"))))

@app.post("/api/miniapp/all")
def miniapp_all():
    if not _admin_ok(): return jsonify(ok=False,error="Unauthorized"),403
    import miniapp as ma
    body=request.get_json(silent=True) or {}; enabled=bool(body.get("enabled"))
    for f in ma.FEATURES:
        try: f[6](enabled)
        except Exception: pass
    return jsonify(ok=True,state=ma.state())

@app.get("/api/miniapp/stats")
def miniapp_stats():
    if not _admin_ok(): return jsonify(ok=False,error="Unauthorized"),403
    import miniapp as ma
    return jsonify(ok=True, **ma.stats())

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False, use_reloader=False, threaded=True)

def keep_alive(): Thread(target=run, name="keep-alive", daemon=True).start()
