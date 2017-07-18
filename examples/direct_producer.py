# direct_producer.py

import mooq
import asyncio
import random

async def main():
    conn = await mooq.connect(host="localhost",
                              port=5672,
                              broker="rabbit")
    chan = await conn.create_channel()

    await chan.register_producer(exchange_name="log",
                                 exchange_type="direct")

    loop.create_task(tick_every_second())
    loop.create_task(publish_randomly(chan))

async def tick_every_second():
    cnt = 0
    while True:
        print("tick producer app {}".format(cnt))
        cnt = cnt + 1
        await asyncio.sleep(1)

async def publish_randomly(chan):
    while True:
        await chan.publish(exchange_name="log",
                           msg="Hello World!",
                           routing_key="greetings")
        print("published!")

        await asyncio.sleep(random.randint(1,10))

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()