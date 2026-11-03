from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import socket
import sys
from collections.abc import Callable

from product.adapter import ExplorerAdapter
from product.config import ProductConfig
from product.errors import ErrorCategory, ProductError
from product.presentation import render_page
from product.validation import invalid_input, parse_target


_CSS = Path(__file__).resolve().parent / "static" / "explorer.css"
_HEADERS = (
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Cache-Control", "no-store"),
    ("Content-Security-Policy", "default-src 'none'; style-src 'self'; base-uri 'none'; "
     "form-action 'self'; frame-ancestors 'none'"),
)


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


def handle_request(
    adapter: ExplorerAdapter, method: str, target: str, host: str, port: int,
) -> Response:
    content_type = "text/html; charset=utf-8"
    additional: tuple[tuple[str, str], ...] = ()
    adapter.status()
    if host not in (f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"):
        status = 400
        body = render_page(adapter.home(invalid_input())).encode("utf-8")
    elif method not in ("GET", "HEAD"):
        status = 405
        additional = (("Allow", "GET, HEAD"),)
        body = render_page(adapter.home(ProductError(
            ErrorCategory.INVALID_INPUT, "input", "Only GET and HEAD are supported.",
        ))).encode("utf-8")
    else:
        parsed = parse_target(target)
        if isinstance(parsed, ProductError):
            status = 400
            body = render_page(adapter.home(parsed)).encode("utf-8")
        else:
            path, selection = parsed
            if path == "/static/explorer.css":
                status = 200
                content_type = "text/css; charset=utf-8"
                body = _CSS.read_bytes()
            else:
                page = adapter.home() if path == "/" else (
                    adapter.load_verse(selection) if path == "/verse" and selection is not None
                    else adapter.home(ProductError(ErrorCategory.ABSENT, "selection", "Route not present."))
                )
                status = 200
                if page.error is not None:
                    status = {
                        ErrorCategory.ABSENT: 404,
                        ErrorCategory.INVALID_INPUT: 400,
                        ErrorCategory.UNSUPPORTED: 400,
                        ErrorCategory.SOURCE_STORE_ERROR: 500,
                    }.get(page.error.category, 200)
                body = render_page(page).encode("utf-8")
    headers = (("Content-Type", content_type), ("Content-Length", str(len(body))), *_HEADERS, *additional)
    return Response(status, headers, b"" if method == "HEAD" else body)


def create_server(config: ProductConfig, adapter: ExplorerAdapter | None = None) -> HTTPServer:
    explorer = ExplorerAdapter(config) if adapter is None else adapter

    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            hosts = self.headers.get_all("Host", [])
            response = handle_request(explorer, self.command, self.path,
                                      hosts[0] if len(hosts) == 1 else "", self.server.server_port)
            self.send_response(response.status)
            for name, value in response.headers:
                self.send_header(name, value)
            self.end_headers()
            if response.body:
                self.wfile.write(response.body)

        do_GET = _respond
        do_HEAD = _respond
        do_POST = _respond
        do_PUT = _respond
        do_PATCH = _respond
        do_DELETE = _respond
        do_OPTIONS = _respond
        do_TRACE = _respond
        do_CONNECT = _respond

        def __getattr__(self, name: str) -> Callable[[], None]:
            if name.startswith("do_"):
                return self._respond
            raise AttributeError(name)

        def log_message(self, format: str, *args: object) -> None:
            print(f"HTTP {self.command} response", file=sys.stderr)

    class LoopbackServer(HTTPServer):
        address_family = socket.AF_INET6 if config.host == "::1" else socket.AF_INET

    return LoopbackServer((config.host, config.port), Handler)
