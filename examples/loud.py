import mooq
import asyncio

#the callback to run
async def yell_it(resp):
    print(resp['msg'].upper())

async def main(loop):
    conn = await mooq.connect(
                    host="localhost",
                    port=5672,
                    broker="rabbit")

    chan = await conn.create_channel()

    await chan.register_consumer( 
            exchange_name="in2com_log",
            exchange_type="direct",
            routing_keys=["greetings","goodbyes"],
            callback = yell_it)

    loop.create_task(tick_every_second())
    loop.create_task(conn.process_events())


async def tick_every_second():
    cnt = 0
    while True:
        print("tick loud {}".format(cnt))
        cnt = cnt + 1
        await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.create_task(main(loop))
loop.run_forever()


