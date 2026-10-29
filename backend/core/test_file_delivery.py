import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from django.test import SimpleTestCase
from core.file_delivery import byte_range, private_file_response


class RangeTests(SimpleTestCase):
    def test_single_ranges_suffix_empty_and_malformed(self):
        for header, expected in ((None, (0, 9, 200)), ('bytes=2-4', (2, 4, 206)),
                                 ('bytes=-3', (7, 9, 206)), ('bytes=8-', (8, 9, 206)),
                                 ('bytes=0-999', (0, 9, 206))):
            self.assertEqual(byte_range(header, 10), expected)
        for header in ('bytes=-0', 'bytes=20-', 'bytes=5-2', 'bytes=-', 'bytes=1-2,3-4', 'bytes='+'1'*1000+'-'):
            with self.assertRaises(ValueError):
                byte_range(header, 10)
        self.assertEqual(byte_range(None, 0), (0, -1, 200))
        with self.assertRaises(ValueError):
            byte_range('bytes=0-', 0)

    def test_head_and_416_do_not_open_file_and_preserve_private_headers(self):
        def unexpected(*args):
            raise AssertionError('File should not be opened')
        for header, status in (('bytes=2-4', 206), ('bytes=100-', 416), (None, 200)):
            response = private_file_response(SimpleNamespace(open=unexpected), method='HEAD', range_header=header,
                size=10, content_type='video/mp4', headers={'Cache-Control': 'private, no-store'})
            self.assertEqual(response.status_code, status)
            self.assertEqual(response['Cache-Control'], 'private, no-store')


class StreamingTests(IsolatedAsyncioTestCase):
    async def test_first_chunk_does_not_read_whole_file_and_disconnect_closes(self):
        class Measured(BytesIO):
            read_bytes = 0
            def read(self, size):
                data = super().read(size)
                self.read_bytes += len(data)
                return data
        handle = Measured(b'x' * 1048576)
        response = private_file_response(SimpleNamespace(open=lambda mode: handle), method='GET', range_header=None,
            size=1048576, content_type='video/mp4', headers={'Cache-Control': 'private, no-store'})
        self.assertTrue(response.is_async)
        iterator = aiter(response.streaming_content)
        self.assertEqual(len(await anext(iterator)), 65536)
        self.assertEqual(handle.read_bytes, 65536)
        await iterator.aclose()
        response.close()
        self.assertTrue(handle.closed)

    async def test_range_contents_are_exact(self):
        response = private_file_response(SimpleNamespace(open=lambda mode: BytesIO(b'0123456789')), method='GET',
            range_header='bytes=2-4', size=10, content_type='video/mp4', headers={})
        self.assertEqual(b''.join([block async for block in response.streaming_content]), b'234')
        self.assertEqual(response['Content-Range'], 'bytes 2-4/10')
        self.assertEqual(response['Content-Length'], '3')
