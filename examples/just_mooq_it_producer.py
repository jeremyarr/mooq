#example consumer in "Just mooq it" section of docs

# producer.py

import mooq

conn = mooq.connect(host="localhost",
                              port=5672,
                              broker="rabbit")
chan = conn.create_channel()

chan.register_producer(exchange_name="log",
                       exchange_type="direct")

chan.publish(exchange_name="log",
             msg="Hello World!",
             routing_key="greetings")

print("published!")


# #ideal API

# async def main():
#     conn = await mooq.connect(host="localhost",
#                               port=5672,
#                               broker="rabbit")
#     chan = await conn.create_channel()

#     await chan.register_producer(exchange_name="log",
#                                  exchange_type="direct")

#     await chan.publish(exchange_name="log",
#                        msg="Hello World!",
#                        routing_key="greetings")

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())