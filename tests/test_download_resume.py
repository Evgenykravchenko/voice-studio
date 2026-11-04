import contextlib
import errno
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error

import httpx
from voice_cloner import models


class DownloadResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.payload = b'local-anonymous-model' * 120_000
        self.entry = {
            'id': 'test-model', 'name': 'Test', 'task': 'transcription',
            'repo': 'test/model', 'revision': 'pinned', 'sizeBytes': len(self.payload),
            'files': [{'path': 'weights.bin', 'size': len(self.payload),
                       'sha256': hashlib.sha256(self.payload).hexdigest()}],
        }
        for mock in [patch.object(models, 'CATALOG', [self.entry]),
                     patch.object(models.time, 'sleep'),
                     patch.dict(models.os.environ),
                     contextlib.redirect_stdout(io.StringIO()),
                     contextlib.redirect_stderr(io.StringIO())]:
            mock.__enter__()
            self.addCleanup(mock.__exit__, None, None, None)

    def test_hub_connection_reset_recovers_without_force_or_selection_change(self):
        target = models.file_path(self.entry, self.entry['files'][0], self.root)
        target.parent.mkdir(parents=True)
        partial = target.with_suffix('.incomplete')
        attempts = []

        def hub(**kwargs):
            attempts.append(kwargs)
            if len(attempts) == 1:
                partial.write_bytes(self.payload[:1234])
                raise httpx.ReadError('Connection reset by peer')
            self.assertEqual(self.payload[:1234], partial.read_bytes())
            target.write_bytes(partial.read_bytes() + self.payload[1234:])
            partial.unlink()
            return str(target)

        with patch('huggingface_hub.hf_hub_download', side_effect=hub):
            models.download('test-model', self.root, prepare=False)
        self.assertEqual(2, len(attempts))
        self.assertTrue(all(c['force_download'] is False and c['token'] is False for c in attempts))
        self.assertTrue(models.installed(self.entry, self.root))
        self.assertFalse((self.root / 'data/studio/models/selection.json').exists())

    def test_exhausted_hub_transfer_keeps_validation_pending_and_partial(self):
        target = models.file_path(self.entry, self.entry['files'][0], self.root)
        target.parent.mkdir(parents=True)
        partial = target.with_suffix('.incomplete')
        partial.write_bytes(self.payload[:321])
        with patch('huggingface_hub.hf_hub_download', side_effect=httpx.ReadError('reset')) as hub:
            with self.assertRaises(httpx.ReadError):
                models.download('test-model', self.root, prepare=False)
        self.assertEqual(3, hub.call_count)
        self.assertEqual(self.payload[:321], partial.read_bytes())
        self.assertTrue(models.validation_marker(self.entry, self.root).exists())
        self.assertFalse(models.installed(self.entry, self.root))

    def test_auth_missing_files_certificate_and_disk_errors_do_not_retry(self):
        request = httpx.Request('GET', 'https://example.invalid/weights')
        certificate = ssl.SSLCertVerificationError(1, 'certificate verification failed')
        wrapped = httpx.ConnectError('TLS failed')
        wrapped.__cause__ = certificate
        errors = [
            *[httpx.HTTPStatusError('access', request=request, response=httpx.Response(code, request=request)) for code in [401, 403, 404]],
            urllib.error.HTTPError('https://example.invalid', 403, 'forbidden', {}, None),
            urllib.error.URLError(certificate), wrapped,
            OSError(errno.ENOSPC, 'No space left'), BrokenPipeError(errno.EPIPE, 'Progress consumer closed'), ValueError('invalid catalog'),
        ]
        for error in errors:
            with self.subTest(error=repr(error)), patch('huggingface_hub.hf_hub_download', side_effect=error) as hub:
                with self.assertRaises(type(error)):
                    models.download('test-model', self.root, prepare=False)
                self.assertEqual(1, hub.call_count)
                self.assertFalse(models.installed(self.entry, self.root))

    def test_direct_http_disconnect_resumes_range_and_verifies_hash(self):
        payload = self.payload
        ranges = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                value = self.headers.get('Range')
                ranges.append(value)
                offset = int(value.removeprefix('bytes=').removesuffix('-')) if value else 0
                self.send_response(206 if offset else 200)
                self.send_header('Content-Length', str(len(payload) - offset))
                if offset:
                    self.send_header('Content-Range', f'bytes {offset}-{len(payload)-1}/{len(payload)}')
                self.end_headers()
                if len(ranges) == 1:
                    self.wfile.write(payload[:1_100_000])
                    self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR)
                else:
                    self.wfile.write(payload[offset:])

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.entry.update(artifactSource='url')
            self.entry['files'][0]['url'] = f'http://127.0.0.1:{server.server_port}/weights'
            models.download('test-model', self.root, prepare=False)
            self.assertEqual([None, 'bytes=1100000-'], ranges)
            target = models.file_path(self.entry, self.entry['files'][0], self.root)
            self.assertEqual(payload, target.read_bytes())
            self.assertFalse(target.with_suffix('.part').exists())
            self.assertTrue(models.installed(self.entry, self.root))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_transferred_corrupt_file_never_becomes_ready(self):
        target = models.file_path(self.entry, self.entry['files'][0], self.root)
        target.parent.mkdir(parents=True)
        target.write_bytes(b'x' * len(self.payload))
        with patch('huggingface_hub.hf_hub_download', return_value=str(target)) as hub:
            with self.assertRaisesRegex(ValueError, 'Проверка файлов'):
                models.download('test-model', self.root, prepare=False)
        self.assertEqual(2, hub.call_count)
        self.assertFalse(models.installed(self.entry, self.root))


if __name__ == '__main__':
    unittest.main()
