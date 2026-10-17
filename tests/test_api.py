import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import app, jobs  # noqa: E402


class MiniShellApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_foreground_pwd(self):
        response = self.client.post("/api/execute", json={"command": "pwd", "background": False})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("job", body)
        self.assertEqual(body["job"]["status"], "COMPLETED")
        self.assertTrue(body["job"]["stdout"].strip())

    def test_unsupported_command_rejected(self):
        response = self.client.post("/api/execute", json={"command": "invalid_command_xyz"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("not allowed", response.get_json()["error"])

    def test_shell_operator_rejected(self):
        response = self.client.post("/api/execute", json={"command": "pwd; whoami"})
        self.assertEqual(response.status_code, 400)

    def test_workspace_cat(self):
        response = self.client.post("/api/execute", json={"command": "cat sample.txt"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome to the Mini Linux Shell workspace", response.get_json()["job"]["stdout"])

    def test_path_traversal_rejected(self):
        response = self.client.post("/api/execute", json={"command": "cat ../README.md"})
        self.assertEqual(response.status_code, 400)

    def test_background_and_stop(self):
        response = self.client.post("/api/execute", json={"command": "sleep 20", "background": True})
        self.assertEqual(response.status_code, 201)
        job = response.get_json()["job"]
        self.assertEqual(job["status"], "RUNNING")
        stop = self.client.post(f"/api/jobs/{job['id']}/stop", json={})
        self.assertEqual(stop.status_code, 200)
        # Allow SIGTERM to be handled and the process status to be reaped.
        time.sleep(0.15)
        self.client.get("/api/jobs")

    def test_help(self):
        response = self.client.get("/api/help")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sleep", response.get_json()["commands"])


if __name__ == "__main__":
    unittest.main()
