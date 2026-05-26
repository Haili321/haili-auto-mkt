"""Lark OAuth helper. Run once per machine to grant a user token.

Starts a local web server on http://localhost:9000/callback, opens the
authorisation URL in your default browser, waits for the redirect, and
caches the resulting refresh token via LarkClient.

Usage:
    python3 lark_auth.py

After this runs successfully, you do not need to run it again unless the
refresh token is revoked.
"""
from __future__ import annotations

import http.server
import subprocess
import threading
import urllib.parse

from lark_client import LarkClient

REDIRECT_URI = "http://localhost:9000/callback"
auth_code: str | None = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h1>Authorised</h1><p>You can close this tab and return to the terminal.</p>".encode(
                    "utf-8"
                )
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h1>Authorisation failed</h1><p>No code received.</p>".encode("utf-8")
            )

    def log_message(self, format, *args):
        pass


# Curated set of common User-token scopes. The Lark OAuth URL is capped at
# roughly 4000 characters, so add scopes here only if you actually use the
# corresponding API. Leaving this list empty (or removing the scope param
# below) makes Lark show every scope already configured on your app.
USER_SCOPES: list[str] = [
    # docs
    "docx:document",
    "docx:document:readonly",
    "docs:doc",
    "docs:doc:readonly",
    "docs:document.content:read",
    "drive:drive",
    "drive:drive:readonly",
    "drive:file",
    "drive:file:readonly",
    "drive:file:download",
    "drive:file:upload",
    "drive:export:readonly",
    # sheets
    "sheets:spreadsheet",
    "sheets:spreadsheet:read",
    "sheets:spreadsheet:readonly",
    # messaging
    "im:message",
    "im:message:readonly",
    "im:message.send_as_user",
    "im:chat",
    "im:chat:readonly",
    # search
    "search:docs:read",
    "search:message",
    # contacts (for sending by email)
    "contact:contact.base:readonly",
    "contact:user.email:readonly",
]


def main():
    client = LarkClient()

    server = http.server.HTTPServer(("localhost", 9000), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    params = urllib.parse.urlencode({
        "app_id": client.app_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
    })
    auth_url = f"https://open.larksuite.com/open-apis/authen/v1/authorize?{params}"
    print("Opening browser for authorisation (using all scopes configured on the app).")
    print(f"URL length: {len(auth_url)} chars")
    print(f"If the browser does not open, visit manually:\n{auth_url}\n")
    subprocess.run(["open", auth_url])

    print("Waiting for callback...")
    thread.join(timeout=120)
    server.server_close()

    if auth_code:
        print(f"Got code: {auth_code[:10]}...")
        client.auth_with_code(auth_code)
        print("\nDone. Token cached; no need to run this again.")
    else:
        print("Timed out or no code received. Try again.")


if __name__ == "__main__":
    main()
