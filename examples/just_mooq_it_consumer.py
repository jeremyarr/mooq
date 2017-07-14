#example consumer in "Just mooq it" section of docs

#consumer.py

import mooq

#the callback to run
def yell_it(resp):
    print(resp['msg'].upper())

conn = mooq.connect(host="localhost",
                    port=5672,
                    broker="rabbit")
chan = conn.create_channel()

chan.register_consumer( queue_name="my_queue",
                        exchange_name="log",
                        exchange_type="direct",
                        routing_keys=["greetings","goodbyes"],
                        callback = yell_it)

#blocking
print("waiting for first event...")
conn.process_events()


# #ideal API

# #the callback to run
# async def yell_it(resp):
#     print(resp['msg'].upper())

# async def main(loop):
#     conn = await mooq.connect(host="localhost",
#                         port=5672,
#                         broker="rabbit")
#     chan = await conn.create_channel()

#     await chan.register_consumer( 
#                             exchange_name="log",
#                             exchange_type="direct",
#                             routing_keys=["greetings","goodbyes"],
#                             callback = yell_it)

#     loop.create_task(conn.process_events())

# loop = asyncio.get_event_loop()
# loop.create_task(main(loop))
# loop.run_forever()


