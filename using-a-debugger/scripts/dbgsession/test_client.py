import socket
import threading
from pathlib import Path

import pytest
from client import _read_port, send_verb


def test_read_port_success(tmp_path: Path):
    port_file = tmp_path / "port"
    port_file.write_text("12345\n")
    assert _read_port(tmp_path, retries=2, interval=0.01) == 12345


def test_read_port_timeout(tmp_path: Path):
    with pytest.raises(TimeoutError, match="port file not found"):
        _read_port(tmp_path, retries=2, interval=0.01)


def test_send_verb(tmp_path: Path):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    (tmp_path / "port").write_text(str(port))

    received_lines = []

    def _server_thread():
        conn, _ = server_sock.accept()
        with conn:
            data = conn.recv(1024).decode()
            received_lines.append(data)
            conn.sendall(b"response_ok\n")
        server_sock.close()

    thread = threading.Thread(target=_server_thread)
    thread.start()

    reply = send_verb(tmp_path, "local a")
    thread.join()

    assert reply == "response_ok\n"
    assert received_lines == ["local a\n"]
