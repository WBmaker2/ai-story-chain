#!/usr/bin/env python3
import json
import unittest
from email.message import Message
from io import BytesIO
from unittest import mock
from urllib.parse import unquote

import server


class StoryTrainServerTests(unittest.TestCase):
    def run_handler(self, method, path, body=b"", headers=None):
        handler = object.__new__(server.StoryTrainHandler)
        handler.rfile = BytesIO(body)
        handler.wfile = BytesIO()
        handler.headers = Message()
        for key, value in (headers or {}).items():
            handler.headers[key] = value
        handler.path = path
        handler.command = method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.client_address = ("127.0.0.1", 12345)
        handler.server = mock.Mock()

        getattr(handler, f"do_{method}")()
        raw = handler.wfile.getvalue()
        head, _, data = raw.partition(b"\r\n\r\n")
        status = int(head.split(b" ", 2)[1])
        return status, head, data

    def test_serves_index(self):
        status, _headers, data = self.run_handler("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn(b"<!doctype html>", data.lower())

    def test_does_not_serve_env_file(self):
        status, _headers, _data = self.run_handler("GET", "/.env")

        self.assertEqual(status, 404)

    def test_does_not_serve_markdown_docs(self):
        status, _headers, _data = self.run_handler("GET", "/DEPLOY.md")

        self.assertEqual(status, 404)

    def test_rejects_oversized_json_body(self):
        body = b"{" + (b" " * 9000)
        status, _headers, data = self.run_handler(
            "POST",
            "/api/generate-image",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 413)
        self.assertIn("request body too large", data.decode("utf-8"))

    def test_rejects_too_long_sentence_without_generating_image(self):
        body = json.dumps({"sentence": "가" * 501}).encode("utf-8")

        with mock.patch.object(
            server.StoryTrainHandler,
            "generate_image_with_fallback",
            side_effect=AssertionError("image generation should not be called"),
        ):
            status, _headers, data = self.run_handler(
                "POST",
                "/api/generate-image",
                body=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
            )

        self.assertEqual(status, 400)
        self.assertIn("sentence is too long", data.decode("utf-8"))


class PollinationsPromptTests(unittest.TestCase):
    def test_prompt_prefix_without_trailing_space_still_separates_sentence(self):
        captured = {}

        class FakeResponse:
            headers = {"Content-Type": "image/png"}

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"fake-image"

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            return FakeResponse()

        with mock.patch.dict(server.os.environ, {"PROMPT_PREFIX": "scene:"}, clear=False):
            with mock.patch.object(server.request, "urlopen", side_effect=fake_urlopen):
                handler = object.__new__(server.StoryTrainHandler)
                data_url = handler.generate_with_pollinations("기차가 달려요")

        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        self.assertIn("scene: 기차가 달려요", unquote(captured["url"]))


if __name__ == "__main__":
    unittest.main()
