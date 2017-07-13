#example consumer in "Just mooq it" section of docs

# producer.py

import mooq

conn_resource = mooq.create_connection_resource(host="localhost",
                                                port=5672,
                                                broker="rabbit")

chan_resource = mooq.create_channel_resource(conn_resource)

#the channel is only able to be used within the context manager
#this prevents two threads communicating on the same 
#channel at the same time.
with chan_resource.access() as chan:
    chan.register_producer(exchange_name="log",
                           exchange_type="direct")

    chan.publish(exchange_name="log",
                 msg="Hello World!",
                 routing_key="greetings")
    print("published!")

#resources must be closed after use
conn_resource.close()
chan_resource.close()