"""Security headers on every response (RNF5).

Nginx adds HSTS in production; these go in the app itself so they hold even
without the proxy (local, tests, a misconfigured server).
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    # Answers carry tokens and presigned URLs: never keep them in a cache.
    (b"cache-control", b"no-store"),
    (b"cross-origin-resource-policy", b"same-origin"),
    (b"permissions-policy", b"camera=(), geolocation=(), microphone=()"),
]
# A JSON API loads nothing; only the documentation pages need scripts and styles.
_API_CSP = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
_DOCS_PATHS = ("/docs", "/redoc")


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_docs = scope["path"].startswith(_DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                present = {name for name, _ in message.get("headers", [])}
                extra = [h for h in _HEADERS if h[0] not in present]
                if not is_docs:
                    extra.append(_API_CSP)
                message["headers"] = [*message.get("headers", []), *extra]
            await send(message)

        await self.app(scope, receive, send_with_headers)
