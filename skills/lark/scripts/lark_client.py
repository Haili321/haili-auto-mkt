"""Lark (Feishu international) API client.

Supports both tenant access tokens (app-only, no login) and user OAuth tokens
with automatic refresh. Surfaces document, spreadsheet, drive, and message
APIs through a single `LarkClient` class.

Config and token cache locations:
- Config: `$LARK_CONFIG`, else `./lark_config.json`. Must contain
  `{"app_id": "...", "app_secret": "..."}`.
- Token cache: `$LARK_TOKEN_CACHE`, else `./.lark_tokens.json`.

Both files are gitignored by default in this repo. Do not commit them.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

BASE_URL = "https://open.larksuite.com/open-apis"


def _config_path() -> Path:
    override = os.environ.get("LARK_CONFIG")
    if override:
        return Path(override)
    return Path.cwd() / "lark_config.json"


def _token_cache_path() -> Path:
    override = os.environ.get("LARK_TOKEN_CACHE")
    if override:
        return Path(override)
    return Path.cwd() / ".lark_tokens.json"


class LarkClient:
    def __init__(self, app_id=None, app_secret=None):
        if app_id is None or app_secret is None:
            config = self._load_config()
            app_id = config["app_id"]
            app_secret = config["app_secret"]

        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_token = None
        self._tenant_token_expire = 0
        self._user_token = None
        self._refresh_token = None
        self._user_token_expire = 0
        self._load_cached_tokens()

    # ── Config ────────────────────────────────────────────────

    def _load_config(self):
        path = _config_path()
        if not path.exists():
            template = {"app_id": "YOUR_APP_ID", "app_secret": "YOUR_APP_SECRET"}
            path.write_text(json.dumps(template, indent=2))
            raise FileNotFoundError(
                f"Wrote a config template to {path}. Fill in app_id and app_secret."
            )
        return json.loads(path.read_text())

    # ── Token cache ───────────────────────────────────────────

    def _load_cached_tokens(self):
        path = _token_cache_path()
        if not path.exists():
            return
        data = json.loads(path.read_text())
        self._refresh_token = data.get("refresh_token")
        self._user_token = data.get("user_access_token")
        self._user_token_expire = data.get("user_token_expire", 0)
        if self._refresh_token and time.time() > self._user_token_expire:
            try:
                self._do_refresh_user_token()
            except Exception:
                pass

    def _save_cached_tokens(self):
        data = {
            "refresh_token": self._refresh_token,
            "user_access_token": self._user_token,
            "user_token_expire": self._user_token_expire,
        }
        _token_cache_path().write_text(json.dumps(data, indent=2))

    # ── Tenant token (no login) ───────────────────────────────

    def get_tenant_token(self):
        """Get an app-level tenant_access_token. No user login required."""
        if self._tenant_token and time.time() < self._tenant_token_expire:
            return self._tenant_token

        resp = requests.post(
            f"{BASE_URL}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Failed to get tenant token: {data}")

        self._tenant_token = data["tenant_access_token"]
        self._tenant_token_expire = time.time() + data.get("expire", 7200) - 60
        return self._tenant_token

    # ── User OAuth (login once, refresh forever) ──────────────

    def get_auth_url(self, redirect_uri="http://localhost:9000/callback"):
        """Build the first-time authorisation URL."""
        url = (
            f"https://open.larksuite.com/open-apis/authen/v1/authorize"
            f"?app_id={self.app_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
        )
        print(f"Open this URL in a browser to authorise:\n{url}")
        return url

    def auth_with_code(self, code):
        """Exchange an auth code for a user token. Call once after browser approval."""
        resp = requests.post(
            f"{BASE_URL}/authen/v1/oidc/access_token",
            headers={"Authorization": f"Bearer {self.get_tenant_token()}"},
            json={"grant_type": "authorization_code", "code": code},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Authorisation failed: {data}")

        token_data = data["data"]
        self._user_token = token_data["access_token"]
        self._refresh_token = token_data["refresh_token"]
        self._user_token_expire = time.time() + token_data.get("expires_in", 7200) - 60
        self._save_cached_tokens()
        print("User authorised. Token cached; no need to log in again.")
        return self._user_token

    def _do_refresh_user_token(self):
        """Refresh the user token using the cached refresh token."""
        resp = requests.post(
            f"{BASE_URL}/authen/v1/oidc/refresh_access_token",
            headers={"Authorization": f"Bearer {self.get_tenant_token()}"},
            json={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Token refresh failed: {data}")

        token_data = data["data"]
        self._user_token = token_data["access_token"]
        self._refresh_token = token_data["refresh_token"]
        self._user_token_expire = time.time() + token_data.get("expires_in", 7200) - 60
        self._save_cached_tokens()
        return self._user_token

    def get_user_token(self):
        """Get a fresh user token; refresh automatically on expiry."""
        if self._user_token and time.time() < self._user_token_expire:
            return self._user_token
        if self._refresh_token:
            return self._do_refresh_user_token()
        raise Exception(
            "No user token. Run get_auth_url() and auth_with_code() first."
        )

    # ── HTTP helpers ──────────────────────────────────────────

    def _request(self, method, path, as_user=False, **kwargs):
        token = self.get_user_token() if as_user else self.get_tenant_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def _api(self, method, path, as_user=False, **kwargs):
        resp = self._request(method, path, as_user=as_user, **kwargs)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"API error: {data}")
        return data.get("data", data)

    # ── Document operations ───────────────────────────────────

    def get_doc_content(self, document_id, as_user=False):
        """Read full document content in docx format."""
        return self._api("GET", f"/docx/v1/documents/{document_id}", as_user=as_user)

    def get_doc_blocks(self, document_id, as_user=False):
        """Get all content blocks in a document."""
        return self._api(
            "GET", f"/docx/v1/documents/{document_id}/blocks", as_user=as_user
        )

    def get_doc_raw_content(self, document_id, as_user=False):
        """Get document plain-text content."""
        return self._api(
            "GET",
            f"/docx/v1/documents/{document_id}/raw_content",
            as_user=as_user,
        )

    def create_doc(self, title, folder_token=None, as_user=False):
        """Create a new docx document."""
        body = {"title": title}
        if folder_token:
            body["folder_token"] = folder_token
        return self._api("POST", "/docx/v1/documents", json=body, as_user=as_user)

    def create_block(self, document_id, block_id, children, index=-1, as_user=False):
        """Append content blocks. Note: text blocks use 'text' not 'paragraph'."""
        body = {"children": children}
        if index >= 0:
            body["index"] = index
        return self._api(
            "POST",
            f"/docx/v1/documents/{document_id}/blocks/{block_id}/children",
            json=body,
            params={"document_revision_id": "-1"},
            as_user=as_user,
        )

    def add_text(self, document_id, content, as_user=False):
        """Shortcut: append a paragraph of text to the end of a document."""
        return self.create_block(
            document_id,
            document_id,
            [{
                "block_type": 2,
                "text": {
                    "elements": [{"text_run": {"content": content}}]
                },
            }],
            as_user=as_user,
        )

    # ── Spreadsheet operations ────────────────────────────────

    def get_sheet_values(self, spreadsheet_token, sheet_range, as_user=False):
        """Read a spreadsheet range. sheet_range looks like 'Sheet1!A1:C10'."""
        return self._api(
            "GET",
            f"/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_range}",
            as_user=as_user,
        )

    def update_sheet_values(
        self, spreadsheet_token, sheet_range, values, as_user=False
    ):
        """Write a 2D list of values to a spreadsheet range."""
        body = {
            "valueRange": {
                "range": sheet_range,
                "values": values,
            }
        }
        return self._api(
            "PUT",
            f"/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            json=body,
            as_user=as_user,
        )

    # ── Export / download ─────────────────────────────────────

    def export_doc(self, file_token, file_type="docx", export_format="docx", as_user=False):
        """Create an export task. file_type: doc / sheet / bitable / docx.
        export_format: docx / pdf / xlsx / csv.
        """
        body = {
            "file_extension": export_format,
            "token": file_token,
            "type": file_type,
        }
        return self._api(
            "POST", "/drive/v1/export_tasks", json=body, as_user=as_user
        )

    def get_export_task(self, ticket, file_token, as_user=False):
        """Poll an export task for completion."""
        return self._api(
            "GET",
            f"/drive/v1/export_tasks/{ticket}?token={file_token}",
            as_user=as_user,
        )

    def download_export(self, file_token, ticket, save_path, as_user=False):
        """Wait for an export task to complete, then download the result."""
        for _ in range(30):
            task = self.get_export_task(ticket, file_token, as_user=as_user)
            if task.get("result", {}).get("file_token"):
                break
            time.sleep(1)
        else:
            raise TimeoutError("Export task timed out.")

        download_token = task["result"]["file_token"]
        resp = self._request(
            "GET",
            f"/drive/v1/export_tasks/file/{download_token}/download",
            as_user=as_user,
        )
        Path(save_path).write_bytes(resp.content)
        print(f"Saved to {save_path}")

    # ── Drive / file operations ───────────────────────────────

    def list_files(self, folder_token=None, as_user=False):
        """List files in a drive folder (root if folder_token is None)."""
        params = {}
        if folder_token:
            params["folder_token"] = folder_token
        return self._api(
            "GET", "/drive/v1/files", params=params, as_user=as_user
        )

    def download_file(self, file_token, save_path, as_user=False):
        """Download a file from drive by token."""
        resp = self._request(
            "GET",
            f"/drive/v1/medias/{file_token}/download",
            as_user=as_user,
        )
        Path(save_path).write_bytes(resp.content)
        print(f"Saved to {save_path}")

    # ── Messaging ─────────────────────────────────────────────

    def send_message(self, receive_id, msg_type, content, receive_id_type="open_id", as_user=False):
        """Send a message.

        receive_id_type: open_id / user_id / union_id / email / chat_id.
        msg_type: text / post / image / interactive / share_chat / file / ...
        content: JSON string matching msg_type.
        """
        return self._api(
            "POST",
            "/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json={
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": content,
            },
            as_user=as_user,
        )

    def send_text(self, receive_id, text, receive_id_type="open_id", as_user=False):
        """Shortcut: send a text message."""
        content = json.dumps({"text": text})
        return self.send_message(receive_id, "text", content, receive_id_type, as_user)

    def send_to_chat(self, chat_id, text, as_user=False):
        """Shortcut: send a text message to a chat (group)."""
        return self.send_text(chat_id, text, receive_id_type="chat_id", as_user=as_user)

    def send_to_email(self, email, text, as_user=False):
        """Shortcut: send a text message to a user by email."""
        return self.send_text(email, text, receive_id_type="email", as_user=as_user)

    def list_chats(self, as_user=False):
        """List chats that the user or bot has joined."""
        return self._api("GET", "/im/v1/chats", as_user=as_user)

    def reply_message(self, message_id, msg_type, content, as_user=False):
        """Reply to a specific message."""
        return self._api(
            "POST",
            f"/im/v1/messages/{message_id}/reply",
            json={
                "msg_type": msg_type,
                "content": content,
            },
            as_user=as_user,
        )

    # ── Message search ────────────────────────────────────────

    def search_messages(self, query, page_size=20, as_user=False):
        """Search chat messages."""
        return self._api(
            "POST",
            "/search/v2/message",
            params={"user_id_type": "open_id"},
            json={"query": query, "page_size": page_size},
            as_user=as_user,
        )

    def get_message(self, message_id, as_user=False):
        """Get detailed content for a specific message."""
        return self._api(
            "GET",
            f"/im/v1/messages/{message_id}",
            as_user=as_user,
        )

    def get_chat_messages(self, chat_id, page_size=50, as_user=False):
        """List messages in a chat."""
        return self._api(
            "GET",
            "/im/v1/messages",
            params={
                "container_id_type": "chat",
                "container_id": chat_id,
                "page_size": page_size,
            },
            as_user=as_user,
        )


if __name__ == "__main__":
    client = LarkClient()
    print(
        "LarkClient ready.\n"
        "Run lark_auth.py once to grant a user token, then import LarkClient "
        "from this module."
    )
