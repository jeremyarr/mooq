#example consumer in "Just mooq it" section of docs

#consumer.py

import mooq
import json
import signal
import sys

def gracefully_exit(signum, frame):
    conn_resource.close()
    chan_resource.close()
    print("\n")
    sys.exit(0)

#resources for accessing amqp connections and channels in a thread 
#safe manner
conn_resource = mooq.create_connection_resource(host="localhost",
                                                port=5672,
                                                broker="rabbit")

chan_resource = mooq.create_channel_resource(conn_resource)
signal.signal(signal.SIGINT, gracefully_exit)


#the callback to run
def yell_it(ch, meth, prop, body):
    msg = json.loads(body)
    print(msg.upper())

with chan_resource.access() as chan:
    chan.register_consumer( queue_name="my_queue",
                            exchange_name="log",
                            exchange_type="direct",
                            routing_keys=["greetings","goodbyes"],
                            callback = yell_it)


#wait for events to be received and process them by running
#associated callbacks
with conn_resource.access() as conn:
    print("waiting for first event:")
    conn.process_events()

