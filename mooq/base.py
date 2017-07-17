import threading
import asyncio
from functools import wraps

class ExchangeNotFound(Exception):
    pass

class ConsumerQueueNotFound(Exception):
    pass

class ConsumeTimeout(Exception):
    pass

class NothingToConsume(Exception):
    pass

class BadExchange(Exception):
    pass

class BrokerInternalError(Exception):
    pass

broker_registry = {}


def create_task(coro_obj,loop):
    launched = loop.create_future()
    return loop.create_task(task_wrapper(coro_obj,launched)), launched

async def task_wrapper(coro_obj,launched):
        launched.set_result(True)
        await coro_obj




class Broker(object):
    def __init__(self,*,host,port):
        self.host = host
        self.port = port
        self.name = "{}_{}".format(self.host,self.port)
        broker_registry[self.name] = self

    def close(self):
        raise NotImplementedError

    async def run(self):
        raise NotImplementedError


class Exchange(object):
    def __init__(self,*,name,type_):
        self.name = name
        assert type_ in ["direct","fanout","topic"]
        self.type_ = type_

    def bind(self,queue_name,routing_keys):
        raise NotImplementedError

class Connection(object):
    def __init__(self,*,host,port):
        self.host = host
        self.port = port
        self.conn_lock = TimeoutRLock(1)
        self.connected = False
        self.channels = []
        self.loop = asyncio.get_event_loop()

    async def create_channel(self):
        raise NotImplementedError

    async def connect(self):
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError

    async def process_events(self,num_cycles=None):
        raise NotImplementedError

    def get_broker(self,*,host,port):
        broker_name = "{}_{}".format(host,port)
        return broker_registry[broker_name]


class ConsumerQueue(object):
    def __init__(self,*,name):
        self.name = name

    def get_next_message(self):
        raise NotImplementedError

    def put(self,data):
        raise NotImplementedError

class Channel(object):
    def __init__(self,*,internal_chan,loop):
        self._chan = internal_chan
        self.chan_lock = TimeoutRLock(1)
        self.loop = loop

    async def register_producer(self, *, exchange_name, exchange_type):
        raise NotImplementedError

    async def register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys):
        raise NotImplementedError

    async def publish(self,*,exchange_name, msg, routing_key=''):
        raise NotImplementedError

class TimeoutRLock(object):
    def __init__(self, timeout):
        self.rlock_obj = threading.RLock()
        self.timeout = timeout


    def __enter__(self):
        self.rlock_obj.acquire(timeout=self.timeout)

    def __exit__(self,exc_type, exc_value, tb):
        self.rlock_obj.release()

def lock_channel(func):
    @wraps(func)
    def inner(self,*args,**kwargs):
        with self.chan_lock:
            out = func(self,*args,**kwargs)

            return out

    return inner

def lock_connection(func):
    @wraps(func)
    def inner(self,*args,**kwargs):
        with self.conn_lock:
            out = func(self,*args,**kwargs)

            return out

    return inner

