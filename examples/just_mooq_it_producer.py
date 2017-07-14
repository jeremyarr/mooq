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