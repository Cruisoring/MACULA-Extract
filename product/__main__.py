import sys

from product.config import parse_config
from product.server import create_server


def main() -> int:
    config = parse_config()
    try:
        with create_server(config) as server:
            host = f"[{config.host}]" if config.host == "::1" else config.host
            print(f"Matthew Scripture Structural Explorer: http://{host}:{server.server_port}",
                  flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except OSError as error:
        print(f"Local HTTP server unavailable ({type(error).__name__}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
