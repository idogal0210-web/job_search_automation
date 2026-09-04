"""Quick launcher for the local dashboard sync server."""
import sys
from src.dashboard_server import run_server

if __name__ == '__main__':
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
