from collections import namedtuple
import queue
import uuid
import traceback
import re
import asyncio
from . import base


InMemoryChannelInternal = namedtuple("InMemoryChannelInternal", ["msg_q", "broker_q"])


class InMemoryBroker(base.Broker):
    '''
    Implementation of an in memory broker
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.broker_ctl_q = queue.Queue()
        self.msg_q = queue.Queue()
        self.broker_q = queue.Queue()
        self.exchanges = []
        self.consumer_queues = []

    async def close(self):
        '''
        close the broker
        '''

        self.broker_ctl_q.put("close", block=False)
        await self.not_running

    async def run(self, is_running=None):
        '''
        restarts the broker

        :param is_running: A future set to done once the broker is confirmed
            as being running
        :type is_running: future
        '''

        if not is_running:
            raise ValueError("is running future must be supplied as keyword argument")

        is_running.set_result(None)
        self.not_running = self.loop.create_future()
        while True:
            try:
                broker_ctl_cmd = self.broker_ctl_q.get(block=False)
            except queue.Empty:
                pass
            else:
                if broker_ctl_cmd == "close":
                    self.not_running.set_result(None)
                    break

            try:
                msg = self.msg_q.get(block=False)
            except queue.Empty:
                pass
            else:
                self._handle_msg(msg)

            await asyncio.sleep(0.001)

    def _handle_msg(self, msg):
        try:
            self._command_router(msg)
        except Exception as e:
            tb_str = traceback.format_exc()
            self._put_error(base.BrokerInternalError, msg=tb_str)

    def _command_router(self, msg):
        if msg['command'] == "publish":
            self._route_message_to_consumer_queues(
                msg['exchange_name'],
                msg['msg'],
                msg['routing_key']
            )

        elif msg['command'] == "register_producer":
            self._add_exchange(msg['exchange_name'], msg['exchange_type'])
        elif msg['command'] == "register_consumer":
            self._add_exchange(msg['exchange_name'], msg['exchange_type'])
            self._add_consumer_queue(msg['queue_name'])
            exch = self._get_exchange(msg['exchange_name'])
            if msg['exchange_type'] == "fanout":
                msg['routing_keys'] = [""]

            exch.bind(msg['queue_name'], msg['routing_keys'])

    def _add_exchange(self, name, type_):
        try:
            exch = self._get_exchange(name)
        except base.ExchangeNotFound:
            exch = _InMemoryExchange(name=name, type_=type_)
            self.exchanges.append(exch)
        else:
            if type_ != exch.type_:
                msg = ("tried to declare an exchange of type {}"
                     " when it has already been declared of typ {}"
                     "").format(type_, exch.type_)

                self._put_error(base.BadExchange, msg=msg)

    def _put_error(self, e, msg=""):
        self.broker_q.put({"response": "error",
                           "error": e,
                           "msg": msg}, block=False)

    def _get_exchange(self, name):
        for exch in self.exchanges:
            if exch.name == name:
                return exch

        raise base.ExchangeNotFound

    def _add_consumer_queue(self, name):
        if not self._consumer_queue_exists(name):
            cq = _InMemoryConsumerQueue(name=name)
            self.consumer_queues.append(cq)

    def _get_consumer_queue(self, name):
        for cq in self.consumer_queues:
            if cq.name == name:
                return cq

        raise base.ConsumerQueueNotFound

    def _consumer_queue_exists(self, name):
        try:
            self._get_consumer_queue(name)
            return True
        except base.ConsumerQueueNotFound:
            return False

    def _route_message_to_consumer_queues(self, exchange_name, msg, routing_key):
        try:
            exch = self._get_exchange(exchange_name)
        except base.ExchangeNotFound:
            self._put_error(base.BadExchange)
        else:
            if exch.type_ == "direct":
                self._route_direct(exch, msg, routing_key)
            elif exch.type_ == "topic":
                self._route_topic(exch, msg, routing_key)
            elif exch.type_ == "fanout":
                self._route_fanout(exch, msg)
            else:
                raise NotImplementedError

    def _route_direct(self, exch, msg, routing_key):
        for queue_name, routing_keys in exch.queues.items():
            if routing_key in routing_keys:
                cq = self._get_consumer_queue(queue_name)
                cq.put({"msg": msg, "routing_key": routing_key})

    def _route_topic(self, exch, msg, routing_key):
        for queue_name, routing_keys in exch.queues.items():
            for r in routing_keys:
                pattern = self._regexify(r)
                if pattern.match(routing_key):
                    cq = self._get_consumer_queue(queue_name)
                    cq.put({"msg": msg, "routing_key": routing_key})

    def _route_fanout(self, exch, msg):
        for queue_name in exch.queues:
            cq = self._get_consumer_queue(queue_name)
            cq.put({"msg": msg, "routing_key": ""})

    def _regexify(self, routing_key):
        splitted = routing_key.split(".")
        regex_elements = []
        for k in splitted:
            if k == "*":
                regex_elements.append(".+")
            else:
                regex_elements.append(k)

        regex_str = "\.".join(regex_elements)

        return re.compile(regex_str)


class _InMemoryExchange(base.Exchange):
    '''
    Implementation of an in memory exchange
    '''
    def __init__(self, **kwargs):
        '''
        :param name: name of exchange
        :param type\_: type of exchange. Accepted values are
            "direct", "fanout" or "topic"
        :type name: str
        :type type\_: str
        '''

        super().__init__(**kwargs)
        self.queues = {}

    def bind(self, queue_name, routing_keys):
        '''
        Bind routing keys to a queue

        :param queue_name: The name of the queue to bind
        :param routing_keys: A list of keys to match against to bind to the queue
        :type queue_name: str
        :type routing_keys: [str,]
        '''

        if queue_name not in self.queues:
            self.queues[queue_name] = routing_keys
        else:
            self.queues[queue_name].extend(routing_keys)


class _InMemoryConsumerQueue(base.ConsumerQueue):
    '''
    Implementation of an in memory consumer queue
    '''
    def __init__(self, **kwargs):
        '''
        :param name: the name of the queue
        :type name: str
        '''

        super().__init__(**kwargs)
        self._q = queue.Queue()
        self.callback = None

    def get_next_message(self):
        '''
        Get the next message from the consumer queue.

        :return: a message string

        :raises: :class:`ConsumeTimeout` if no messages on the queue
        '''

        try:
            msg_dict = self._q.get(block=False)
            return msg_dict
        except queue.Empty:
            raise base.ConsumeTimeout

    def put(self, data):
        '''
        Put data directly into the consumer queue

        :param data: data to add
        :type data: str
        '''

        self._q.put(data, block=False)


class InMemoryConnection(base.Connection):
    '''
    Implementation of an in memory connection to a broker
    '''

    def __init__(self, **kwargs):
        '''
        :param host: the hostname of the broker you wish to connect to
        :type host: str
        :param port: the port of the broker you wish to connect to
        :type port: int

        .. note:: must call :meth:`InMemoryConnection.connect` to actually connect to the broker
        '''

        super().__init__(**kwargs)

    async def connect(self):
        '''
        Connect to the InMemory broker
        '''
        self.broker = self.get_broker(host=self.host, port=self.port)
        self.msg_q = self.broker.msg_q
        self.broker_q = self.broker.broker_q

    # @base.lock_connection
    async def create_channel(self):
        '''
        create a channel for multiplexing the connection
        :returns: an :class:`InMemoryChannel` object
        '''
        internal_chan = InMemoryChannelInternal(msg_q=self.msg_q, broker_q=self.broker_q)

        chan = InMemoryChannel(internal_chan=internal_chan, loop=self.loop)
        self.channels.append(chan)
        return chan

    async def close(self):
        '''
        Stop processing events and close the connection to the broker
        '''
        self.connected = False

    async def process_events(self, num_cycles=None):
        '''
        Receive messages from the broker and schedule
        associated callback couroutines.

        :param num_cycles: the number of times to run the
            event processing loop. A value of None
            will cause events to be processed without a cycle limit.
        :type num_cycles: int|None
        '''

        while True:
            for chan in self.channels:
                for queue_name, callback in chan.callbacks.items():
                    cq = self.broker._get_consumer_queue(queue_name)

                    try:
                        msg_dict = cq.get_next_message()
                    except base.ConsumeTimeout:
                        pass
                    else:
                        _, launched = base.create_task(callback(msg_dict), self.loop)
                        await launched

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break


class InMemoryChannel(base.Channel):
    '''
    Implementation of an in memory broker channel
    '''

    def __init__(self, **kwargs):
        '''
        :param internal_chan: the transport specific channel object to use
        :param loop: the event loop

        Typically this class will be instantiated outside the main thread.
        '''
        super().__init__(**kwargs)
        self.callbacks = {}

    # @base.lock_channel
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
        self._chan.msg_q.put(
            {
                "command": "register_producer",
                "exchange_name": exchange_name,
                "exchange_type": exchange_type,
            }, block=False
        )
        await self._handle_broker_responses()

    # @base.lock_channel
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

        if queue_name is None:
            queue_name = str(uuid.uuid4())

        self._chan.msg_q.put(
            {
                "command": "register_consumer",
                "exchange_name": exchange_name,
                "exchange_type": exchange_type,
                "queue_name": queue_name,
                "routing_keys": routing_keys
            }, block=False
        )

        self.callbacks[queue_name] = callback

        await self._handle_broker_responses()

    async def _handle_broker_responses(self):
        await asyncio.sleep(0.01)
        while True:
            try:
                resp = self._chan.broker_q.get(block=False)
            except queue.Empty:
                break
            else:
                if resp['response'] == "error":
                    raise resp['error'](resp['msg'])

            await asyncio.sleep(0.001)

    # @base.lock_channel
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
        self._chan.msg_q.put(
            {
                "command": "publish",
                "exchange_name": exchange_name,
                "msg": msg,
                "routing_key": routing_key,
            }, block=False
        )
        await self._handle_broker_responses()
