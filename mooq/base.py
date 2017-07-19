'''
Base classes, helper functions and custom exceptions for mooq

'''

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


def create_task(coro_obj, loop):
    '''
    wrapper for creating a task that can be used for waiting
    until a task has started.

    :param coro_obj: coroutine object to schedule
    :param loop: event loop
    :returns: a two element tuple where the first element
        is the task object. Awaiting on this will return when
        the coroutine object is done executing. The second element
        is a future that becomes done when the coroutine object is started.

    .. note:: must only be called from within the thread
        where the event loop resides
    '''
    async def task_wrapper(coro_obj, launched):
        launched.set_result(True)
        await coro_obj

    launched = loop.create_future()
    return loop.create_task(task_wrapper(coro_obj, launched)), launched


class Broker(object):
    '''
    Base class for a broker. Not to be used directly.
    '''

    def __init__(self, *, host, port):
        '''
        Add the broker to the registry. Each broker is given
        a unique name of "host_port" in the registry.

        :param host: the hostname of the broker you wish to connect to
        :type host: str
        :param port: the port of the broker you wish to connect to
        :type port: int
        '''

        self.host = host
        self.port = port
        self.name = "{}_{}".format(self.host, self.port)
        broker_registry[self.name] = self
        self.loop = asyncio.get_event_loop()

    async def close(self):
        '''
        close the broker

        :raises: NotImplementedError
        '''
        raise NotImplementedError

    async def run(self, is_running=None):
        '''
        restarts the broker

        :param is_running: A future set to done once the broker is confirmed
            as being running
        :type is_running: future

        :raises: NotImplementedError
        '''
        raise NotImplementedError


class Exchange(object):
    '''
    Base class for an exchange. Not to be used directly.
    '''

    def __init__(self, *, name, type_):
        '''
        :param name: name of exchange
        :param type\_: type of exchange. Accepted values are
            "direct", "fanout" or "topic"
        :type name: str
        :type type\_: str
        '''
        self.name = name
        assert type_ in ["direct", "fanout", "topic"]
        self.type_ = type_

    def bind(self, queue_name, routing_keys):
        '''
        Bind routing keys to a queue

        :param queue_name: The name of the queue to bind
        :param routing_keys: A list of keys to match against to bind to the queue
        :type queue_name: str
        :type routing_keys: [str,]
        :raises: NotImplementedError
        '''
        raise NotImplementedError


class ConsumerQueue(object):
    '''
    Base class for a consumer queue. Not to be used directly.
    '''
    def __init__(self, *, name):
        '''
        :param name: the name of the queue
        :type name: str
        '''

        self.name = name

    def get_next_message(self):
        '''
        Get the next message from the consumer queue.

        :return: a message string

        :raises: :class:`ConsumeTimeout` if no messages on the queue
        '''
        raise NotImplementedError

    def put(self, data):
        '''
        Put data directly into the consumer queue

        :param data: data to add
        :type data: str
        '''
        raise NotImplementedError


class Connection(object):
    '''
    Base class for a connection to a broker. Not to be used directly.
    '''
    def __init__(self, *, host, port):
        '''
        :param host: the hostname of the broker you wish to connect to
        :type host: str
        :param port: the port of the broker you wish to connect to
        :type port: int

        .. note:: must call :meth:`connect` to actually connect to the broker
        '''
        self.host = host
        self.port = port
        self.conn_lock = _TimeoutRLock(1)
        self.connected = False
        self.channels = []
        self.loop = asyncio.get_event_loop()

    async def create_channel(self):
        '''
        create a channel for multiplexing the connection

        :raises NotImplementedError:
        '''
        raise NotImplementedError

    async def connect(self):
        '''
        Connect to the broker

        :raises NotImplementedError:
        '''
        raise NotImplementedError

    async def close(self):
        '''
        Stop processing events and close the connection to the broker

        :raises NotImplementedError:
        '''

        raise NotImplementedError

    async def process_events(self, num_cycles=None):
        '''
        Receive messages from the broker and schedule
        associated callback couroutines.

        :param num_cycles: the number of times to run the
            event processing loop. A value of None or "inf"
            will cause events to be processed without a cycle limit.
        :type num_cycles: int|None|"inf"
        :raises NotImplementedError:
        '''
        raise NotImplementedError

    def get_broker(self, *, host, port):
        '''
        Get the :class:`Broker` object associated with the connection.

        :param host: the hostname of the broker
        :type host: str
        :param port: the port of the broker
        :type port: int

        :return: A :class:`Broker` object
        '''

        broker_name = "{}_{}".format(host, port)
        return broker_registry[broker_name]


class Channel(object):
    '''
    Base class for a channel of a connection. Not to be used directly.
    '''
    def __init__(self, *, internal_chan, loop):
        '''
        :param internal_chan: the transport specific channel object to use
        :param loop: the event loop

        Typically this class will be instantiated outside the main thread.
        '''
        self._chan = internal_chan
        self.chan_lock = _TimeoutRLock(1)
        self.loop = loop

    async def register_producer(self, *, exchange_name, exchange_type):
        '''
        Register a producer on the channel by providing information to
        the broker about the exchange the channel is going to use.

        :param exchange_name: name of the exchange
        :type exchange_name: str
        :param exchange_type: Type of the exchange. Accepted values are "direct",
            "topic" or "fanout"
        :type exchange_type: str
        '''
        raise NotImplementedError

    async def register_consumer(self, queue_name=None, routing_keys=[""], *, exchange_name, exchange_type, callback):

        '''
        Register a consumer on the channel.

        :param exchange_name: name of the exchange
        :param exchange_type: Type of the exchange. Accepted values are "direct",
            "topic" or "fanout"
        :param queue_name: name of the queue. If None, a name will be given
            automatically and the queue will be declared exclusive to the channel,
            meaning it will be deleted once the channel is closed.
        :param callback: The callback to run when a message is placed on the queue that
            matches one of the routing keys
        :param routing_keys: A list of keys to match against. A message will only be sent
            to a consumer if its routing key matches one or more of the routing keys listed

        :type exchange_name: str
        :type exchange_type: str
        :type queue_name: str|None
        :type callback: coroutine
        :type routing_keys: [str,]

        '''
        raise NotImplementedError

    async def publish(self, *, exchange_name, msg, routing_key=''):
        '''
        Publish a message on the channel.

        :param exchange_name: The name of the exchange to send the message to
        :param msg: The message to send
        :param routing_key: The routing key to associated the message with
        :type exchange_name: str
        :type msg: str
        :type routing_key: str
        '''
        raise NotImplementedError


class _TimeoutRLock(object):
    '''
    Context manager for a reentrant Lock with timeout
    '''
    def __init__(self, timeout):
        self.rlock_obj = threading.RLock()
        self.timeout = timeout

    def __enter__(self):
        self.rlock_obj.acquire(timeout=self.timeout)

    def __exit__(self, exc_type, exc_value, tb):
        self.rlock_obj.release()


def lock_channel(func):
    '''
    Deocorator to acquire the channel lock and
    release it after use.
    '''
    @wraps(func)
    def inner(self, *args, **kwargs):
        with self.chan_lock:
            out = func(self, *args, **kwargs)

            return out

    return inner


def lock_connection(func):
    '''
    Deocorator to acquire the connection lock and
    release it after use.
    '''
    @wraps(func)
    def inner(self, *args, **kwargs):
        with self.conn_lock:
            out = func(self, *args, **kwargs)

            return out

    return inner
