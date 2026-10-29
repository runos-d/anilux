from asgiref.sync import async_to_sync


def stream_body(response):
    """Consume small test responses in their native sync/ASGI iterator mode."""
    if not response.is_async:
        return b''.join(response.streaming_content)
    async def consume():
        return b''.join([block async for block in response.streaming_content])
    return async_to_sync(consume)()
