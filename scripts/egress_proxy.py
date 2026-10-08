"""Counts the bytes Neon sends to the refresh, so each step's network transfer is known.

Neon's free plan allows 5 GB of public network transfer a month (it ran out once in
Oct 2026). The refresh's local API connects through this proxy instead of straight to
Neon; it forwards everything untouched (TLS stays end to end) and keeps the running
total of bytes from the database in a file the workflow reads before and after each
step. Neon routes by the endpoint id passed in the connection options, since the
client now sees "localhost" instead of Neon's host name.

    python scripts/egress_proxy.py <neon-host> <port> <counter-file>
"""

from __future__ import annotations

import socket
import sys
import threading
from pathlib import Path

LISTEN_PORT = 6543


def main() -> int:
    host, port, counter = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
    total = [0]
    lock = threading.Lock()
    counter.write_text("0")

    def pipe(source: socket.socket, target: socket.socket, counted: bool) -> None:
        try:
            while data := source.recv(65536):
                if counted:
                    with lock:
                        total[0] += len(data)
                        counter.write_text(str(total[0]))
                target.sendall(data)
        except OSError:
            pass
        finally:
            for side in (source, target):
                try:
                    side.close()
                except OSError:
                    pass

    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", LISTEN_PORT))
    listener.listen(64)
    while True:
        client, _ = listener.accept()
        upstream = socket.create_connection((host, port))
        threading.Thread(
            target=pipe, args=(client, upstream, False), daemon=True
        ).start()
        threading.Thread(
            target=pipe, args=(upstream, client, True), daemon=True
        ).start()


if __name__ == "__main__":
    sys.exit(main())
