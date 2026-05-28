"""
Lightweight aiohttp API server that the Mini App calls.
Runs alongside the PTB bot in the same asyncio event loop.
"""
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path

from aiohttp import web

from config import BOT_TOKEN
from database import get_stats, record_result, get_top_users, get_user_lang, increment_streak, reset_streak

logger = logging.getLogger(__name__)
WEBAPP_DIR = Path(__file__).parent / "webapp"


# ── Telegram initData validation ────────────────────────────────────────────
def _validate_init_data(init_data: str) -> bool:
    """Return True if the Telegram initData signature is valid."""
    if not init_data:
        return False
    try:
        params = dict(p.split("=", 1) for p in init_data.split("&") if "=" in p)
        check = params.pop("hash", None)
        if not check:
            return False
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, check)
    except Exception:
        return False


# ── Routes ────────────────────────────────────────────────────────────────────

async def handle_result(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid json"}, status=400)

    user_id  = str(data.get("user_id", ""))
    username = str(data.get("username", ""))
    game_type = data.get("game_type", "country")   # country / capital / flag
    result    = data.get("result", "wrong")          # correct / wrong / timeout
    init_data = data.get("init_data", "")

    if not user_id:
        return web.json_response({"ok": False, "error": "missing user_id"}, status=400)

    if not BOT_TOKEN.endswith("_dev") and not _validate_init_data(init_data):
        logger.warning("Invalid initData from user %s", user_id)

    if game_type not in ("country", "capital"):
        game_type = "country"
    if result not in ("correct", "wrong", "timeout"):
        result = "wrong"

    if result == "correct":
        record_result(user_id, username, game_type, "correct")
        streak, is_best = increment_streak(user_id, username)
    else:
        # Capital timeout is its own column; everything else is wrong
        if result == "timeout" and game_type == "capital":
            record_result(user_id, username, "capital", "timeout")
        else:
            record_result(user_id, username, game_type, "wrong")
        reset_streak(user_id, username)
        streak, is_best = 0, False

    # Return updated stats so the mini app can sync immediately
    s = get_stats(user_id, username)
    total_correct = s['correct_country'] + s['correct_capital']
    total_wrong   = s['wrong_country']   + s['wrong_capital'] + s['timeout_capital']
    return web.json_response({
        "ok": True,
        "streak": streak,
        "is_best": is_best,
        "correct": total_correct,
        "wrong": total_wrong,
        "total": total_correct + total_wrong,
        "best_streak": s['best_streak'],
    })


async def handle_stats(request: web.Request) -> web.Response:
    user_id = request.rel_url.query.get("user_id", "")
    if not user_id:
        return web.json_response({"error": "missing user_id"}, status=400)
    s = get_stats(user_id, "")
    return web.json_response(s)


async def handle_leaderboard(_: web.Request) -> web.Response:
    rows = get_top_users(10)
    result = [{"name": r[0], "correct": r[1], "total": r[2],
               "pct": round(r[1] / r[2] * 100) if r[2] else 0} for r in rows]
    return web.json_response(result)


async def handle_static(request: web.Request) -> web.Response:
    """Serve webapp/ static files."""
    path = request.match_info.get("path", "index.html") or "index.html"
    file_path = (WEBAPP_DIR / path).resolve()
    if not str(file_path).startswith(str(WEBAPP_DIR.resolve())):
        raise web.HTTPForbidden()
    if not file_path.exists() or not file_path.is_file():
        raise web.HTTPNotFound()
    content_types = {
        ".html": "text/html", ".js": "application/javascript",
        ".css": "text/css", ".json": "application/json",
    }
    ct = content_types.get(file_path.suffix, "application/octet-stream")
    return web.Response(body=file_path.read_bytes(), content_type=ct)


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/api/result",       handle_result)
    app.router.add_get("/api/stats",         handle_stats)
    app.router.add_get("/api/leaderboard",   handle_leaderboard)
    app.router.add_get("/",           lambda r: web.HTTPFound("/app/index.html"))
    app.router.add_get("/app",        lambda r: web.HTTPFound("/app/index.html"))
    app.router.add_get(r"/app/{path:.+}", handle_static)
    return app


async def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("API server running at http://%s:%d/app/", host, port)
