from collections import namedtuple
import queue
import uuid
import traceback
import re
import asyncio
from . import base


InMemoryChannelInternal = namedtuple("InMemoryChannelInternal",["msg_q","broker_q"])


class InMemoryBroker(base.Broker):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.broker_ctl_q = queue.Queue()
        self.msg_q = queue.Queue()
        self.broker_q = queue.Queue()
        self.exchanges = []
        self.consumer_queues = []

    async def close(self):
        self.broker_ctl_q.put("close",block=False)
        await self.not_running

    async def run(self,is_running_fut):
        loop = asyncio.get_event_loop()
        is_running_fut.set_result(None)
        self.not_running = loop.create_future()
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
                self.handle_msg(msg)

            await asyncio.sleep(0.001)


    def handle_msg(self, msg):
        try:
            self.command_router(msg)
        except Exception as e:
            tb_str = traceback.format_exc()
            self.put_error(base.BrokerInternalError,msg=tb_str)

    def command_router(self,msg):
        if msg['command'] == "publish":
            self.route_message_to_consumer_queues(
                                msg['exchange_name'],
                                msg['msg'], 
                                msg['routing_key'] )

        elif msg['command'] == "register_producer":
            self.add_exchange(msg['exchange_name'],msg['exchange_type'])
        elif msg['command'] == "register_consumer":
            self.add_exchange(msg['exchange_name'],msg['exchange_type'])
            self.add_consumer_queue(msg['queue_name'])
            exch = self.get_exchange(msg['exchange_name'])
            if msg['exchange_type'] == "fanout":
                msg['routing_keys'] = [""]

            exch.bind(msg['queue_name'],msg['routing_keys'])

    def add_exchange(self, name, type_):
        try:
            exch = self.get_exchange(name)
        except base.ExchangeNotFound:
            exch = InMemoryExchange(name=name,type_=type_)
            self.exchanges.append(exch)
        else:
            if type_ != exch.type_:
                msg=("tried to declare an exchange of type {}"
                     " when it has already been declared of typ {}"
                     "").format(type_,exch.type_)

                self.put_error(base.BadExchange, msg=msg) 


    def put_error(self,e,msg=""):
        self.broker_q.put({ "response": "error",
                            "error": e,
                            "msg": msg
                            }, block=False)

    def get_exchange(self,name):
        for exch in self.exchanges:
            if exch.name == name:
                return exch

        raise base.ExchangeNotFound


    def add_consumer_queue(self, name):
        if not self.consumer_queue_exists(name):
            cq = InMemoryConsumerQueue(name=name)
            self.consumer_queues.append(cq)

    def get_consumer_queue(self,name):
        for cq in self.consumer_queues:
            if cq.name == name:
                return cq
        
        raise base.ConsumerQueueNotFound

    def consumer_queue_exists(self,name):
        try:
            self.get_consumer_queue(name)
            return True
        except base.ConsumerQueueNotFound:
            return False

    def route_message_to_consumer_queues(self,exchange_name,msg,routing_key):
        try:
            exch = self.get_exchange(exchange_name)
        except base.ExchangeNotFound:
            self.put_error(base.BadExchange)
        else:
            if exch.type_ == "direct":
                self.route_direct(exch,msg,routing_key)
            elif exch.type_ == "topic":
                self.route_topic(exch,msg,routing_key)
            elif exch.type_ == "fanout":
                self.route_fanout(exch,msg)
            else:
                raise NotImplementedError

    def route_direct(self,exch,msg,routing_key):
        for queue_name,routing_keys in exch.queues.items():
            if routing_key in routing_keys:
                cq = self.get_consumer_queue(queue_name)
                cq.put({"msg":msg,"routing_key":routing_key})

    def route_topic(self,exch,msg,routing_key):
        for queue_name,routing_keys in exch.queues.items():
            for r in routing_keys:
                pattern = self.regexify(r)
                if pattern.match(routing_key):
                    cq = self.get_consumer_queue(queue_name)
                    cq.put({"msg":msg,"routing_key":routing_key})

    def route_fanout(self,exch,msg):
        for queue_name in exch.queues:
            cq = self.get_consumer_queue(queue_name)
            cq.put({"msg":msg,"routing_key":""})


    def regexify(self,routing_key):
        splitted = routing_key.split(".")
        regex_elements = []
        for k in splitted:
            if k == "*":
                regex_elements.append(".+")
            else:
                regex_elements.append(k)

        regex_str = "\.".join(regex_elements)

        return re.compile(regex_str)



class InMemoryExchange(base.Exchange):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.queues = {}

    def bind(self,queue_name,routing_keys):
        if queue_name not in self.queues:
            self.queues[queue_name] = routing_keys
        else:
            self.queues[queue_name].extend(routing_keys)

class InMemoryConsumerQueue(base.ConsumerQueue):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._q = queue.Queue()
        self.callback = None

    def get_next_message(self):
        try:
            msg_dict = self._q.get(block=False)
            return msg_dict
        except queue.Empty:
            raise base.ConsumeTimeout

    def put(self,data):
        self._q.put(data, block=False)


class InMemoryConnection(base.Connection):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    async def connect(self):
        self.broker = self.get_broker(host=self.host, port=self.port)
        self.msg_q = self.broker.msg_q
        self.broker_q = self.broker.broker_q
    
    # @base.lock_connection
    async def create_channel(self):
        internal_chan = InMemoryChannelInternal(msg_q=self.msg_q,broker_q=self.broker_q)

        chan = InMemoryChannel(internal_chan=internal_chan,loop=self.loop)
        self.channels.append(chan)
        return chan


    async def close(self):
        self.connected = False

    async def process_events(self,num_cycles=None):
        while True:
            for chan in self.channels:
                for queue_name,callback in chan.callbacks.items():
                    cq = self.broker.get_consumer_queue(queue_name)

                    try:
                        msg_dict = cq.get_next_message()
                    except base.ConsumeTimeout:
                        pass
                    else:
                        _, launched = base.create_task(callback(msg_dict),self.loop)
                        await launched

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break


class InMemoryChannel(base.Channel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.callbacks = {}

    # @base.lock_channel
    async def publish(self,*,exchange_name,msg,routing_key=''):
        self._chan.msg_q.put(
                        {
                        "command":"publish",
                        "exchange_name":exchange_name,
                        "msg":msg,
                        "routing_key":routing_key,
                        }, block=False
                       )
        await self._handle_broker_responses()

    # @base.lock_channel
    async def register_producer(self, *, exchange_name, exchange_type):
        self._chan.msg_q.put(
                        {
                        "command":"register_producer",
                        "exchange_name":exchange_name,
                        "exchange_type":exchange_type,
                        }, block=False
                       )


        await self._handle_broker_responses()

    # @base.lock_channel
    async def register_consumer(self, *, exchange_name, exchange_type, 
                         queue_name, callback, routing_keys=[""]):

        if queue_name is None:
            queue_name = str(uuid.uuid4())

        self._chan.msg_q.put(
                        {
                        "command":"register_consumer",
                        "exchange_name":exchange_name,
                        "exchange_type":exchange_type,
                        "queue_name":queue_name,
                        "routing_keys":routing_keys
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









