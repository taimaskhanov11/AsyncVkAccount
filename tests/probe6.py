import asyncio


async def ticker(delay, to):
    for i in range(to):
        yield (i, delay)
        await asyncio.sleep(delay)


async def run(k):
    # пример асинхронного for
    async for i in ticker(k, 10):
        print(i)


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(run(10), run(1)))
finally:
    loop.close()

