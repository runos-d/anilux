"""Demonstrate sync streaming buffering in the deployed image, without video/DB."""
import asyncio
import json
import warnings
from django.conf import settings
settings.configure(DEFAULT_CHARSET='utf-8')
from django.http import StreamingHttpResponse

async def main():
    produced = []
    def chunks():
        for index in range(128):
            produced.append(index)
            yield bytes(65536)
    response = StreamingHttpResponse(chunks())
    with warnings.catch_warnings(record=True) as warnings_seen:
        iterator = response.__aiter__()
        first = await anext(iterator)
        print(json.dumps({'chunks_produced_before_first_send':len(produced),
                          'total_bytes_consumed':len(produced)*65536,
                          'first_chunk_bytes':len(first),
                          'warnings':[str(row.message) for row in warnings_seen]}))
        await iterator.aclose()

asyncio.run(main())
