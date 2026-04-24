import json
import os
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from admin import daemon_health
from runtime_paths import runtime_path


class DaemonHealthTest(unittest.TestCase):
    def test_daemon_health_reports_paths_when_unreachable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"BU_RUNTIME_DIR": tmpdir}, clear=False):
                runtime_path("log", "test").write_text("first\nlast\n")
                health = daemon_health("test")

        self.assertFalse(health["reachable"])
        self.assertEqual(health["name"], "test")
        self.assertEqual(health["last_log_line"], "last")
        self.assertTrue(health["paths"]["sock"].endswith("bu-test.sock"))
        self.assertTrue(health["paths"]["pid"].endswith("bu-test.pid"))
        self.assertTrue(health["paths"]["log"].endswith("bu-test.log"))

    def test_daemon_health_uses_daemon_protocol_when_reachable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"BU_RUNTIME_DIR": tmpdir}, clear=False):
                sock = runtime_path("sock", "test")
                ready = threading.Event()

                def serve_once():
                    if sock.exists():
                        sock.unlink()
                    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    server.bind(str(sock))
                    server.listen(1)
                    ready.set()
                    conn, _ = server.accept()
                    data = b""
                    while not data.endswith(b"\n"):
                        data += conn.recv(1024)
                    self.assertEqual(json.loads(data), {"meta": "health"})
                    conn.sendall(json.dumps({
                        "reachable": True,
                        "name": "test",
                        "pid": 123,
                        "paths": {"sock": str(sock)},
                        "session_id": "ABC",
                        "session_known": True,
                        "last_log_line": "listening",
                    }).encode() + b"\n")
                    conn.close()
                    server.close()

                t = threading.Thread(target=serve_once)
                t.start()
                self.assertTrue(ready.wait(2))
                health = daemon_health("test")
                t.join(2)

        self.assertTrue(health["reachable"])
        self.assertTrue(health["session_known"])
        self.assertEqual(health["session_id"], "ABC")
        self.assertEqual(health["last_log_line"], "listening")


if __name__ == "__main__":
    unittest.main()
