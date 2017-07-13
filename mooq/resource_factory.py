import threading

from .resource import Resource
from .in_memory import InMemoryConnection
from .rabbit import RabbitMQConnection


def connection(host="localhost",port=5672,broker="rabbit"):
    if broker == "in_memory":
        conn_class = InMemoryConnection
    elif broker == "rabbit":
        conn_class = RabbitMQConnection
    else:
        raise NotImplementedError

    conn_resource = Resource(c_func=conn_class,
                             c_args=(),
                             c_kwargs={"host":host,"port":port}) 
    t = threading.Thread(target=conn_resource.box)
    t.start()
    return conn_resource

def channel(conn_resource):
    with conn_resource.access() as conn:
        chan_resource = Resource(c_func=conn.channel_resource_constructor_func,
                                 c_args=(),
                                 c_kwargs={"conn_resource":conn_resource}) 

    t = threading.Thread(target=chan_resource.box)
    t.start()

    with chan_resource.access() as chan:
        chan.connect()

    with conn_resource.access() as conn:
        conn.channel_resources.append(chan_resource)

    return chan_resource