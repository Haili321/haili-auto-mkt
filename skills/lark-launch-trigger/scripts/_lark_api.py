"""Minimal Lark Open API helpers shared by the trigger scripts.

Standard library only. Reads two JSON config files from the working directory
(or from env-var paths):

  lark_config.json     {"app_id": "cli_...", "app_secret": "..."}   env: LARK_CONFIG
  trigger_config.json  see templates/trigger_config.example.json    env: TRIGGER_CONFIG

Uses the tenant access token (app-only, no login). The app's bot must be in
the target group for send_text to work.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

LARK_BASE = "https://open.larksuite.com/open-apis"
FEISHU_BASE = "https://open.feishu.cn/open-apis"

_token_cache: dict = {"value": None, "expire": 0}


def load_json(env_var: str, default_name: str) -> dict:
    path = Path(os.environ.get(env_var, default_name))
    if not path.exists():
        raise SystemExit(
            f"missing {path}; copy the example from templates/ and fill it in "
            f"(or point {env_var} at it)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def lark_config() -> dict:
    return load_json("LARK_CONFIG", "lark_config.json")


def trigger_config() -> dict:
    return load_json("TRIGGER_CONFIG", "trigger_config.json")


def base_url(cfg: dict | None = None) -> str:
    cfg = cfg or trigger_config()
    return FEISHU_BASE if cfg.get("feishu") else LARK_BASE


def _request(method: str, url: str, payload: dict | None = None,
             token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if body.get("code") not in (0, None):
        raise RuntimeError(f"Lark API error {body.get('code')}: {body.get('msg')} ({url})")
    return body.get("data", body)


def tenant_token() -> str:
    """App-only token, cached until shortly before expiry."""
    if _token_cache["value"] and time.time() < _token_cache["expire"] - 120:
        return _token_cache["value"]
    lc = lark_config()
    url = f"{base_url()}/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = json.dumps({"app_id": lc["app_id"], "app_secret": lc["app_secret"]}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if body.get("code") != 0:
        raise RuntimeError(f"tenant_access_token failed: {body.get('msg')}")
    _token_cache["value"] = body["tenant_access_token"]
    _token_cache["expire"] = time.time() + int(body.get("expire", 7200))
    return _token_cache["value"]


def api(method: str, path: str, params: dict | None = None,
        payload: dict | None = None) -> dict:
    url = f"{base_url()}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return _request(method, url, payload, tenant_token())


def send_text(chat_id: str, text: str) -> dict:
    """Post a plain text message to a group the bot is in."""
    return api("POST", "/im/v1/messages", params={"receive_id_type": "chat_id"},
               payload={"receive_id": chat_id, "msg_type": "text",
                        "content": json.dumps({"text": text}, ensure_ascii=False)})


def bot_open_id() -> str:
    """The open_id of THIS app's bot. Use it to tell real triggers apart:
    only @mentions of this id reach the event subscription."""
    info = api("GET", "/bot/v3/info")
    bot = info.get("bot", info)
    oid = bot.get("open_id", "")
    if not oid:
        raise RuntimeError("could not resolve the app bot's open_id (is the bot enabled?)")
    return oid
