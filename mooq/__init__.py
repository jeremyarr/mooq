from collections import namedtuple
import queue
from contextlib import contextmanager
import uuid
import traceback
import pika
import json
import re
import subprocess
import time

from .__version__ import __version__

def one_plus_one():
    return 2

ResourceQueuePair = namedtuple("ResourceQueuePair",["ret","req"])
InMemoryChannelInternal = namedtuple("InMemoryChannelInternal",["msg_q","broker_q"])

class ResourceNotAvailable(Exception):
    pass

class ReturnTimeout(Exception):
    pass

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

in_memory_broker = None
broker_registry = {}



class Broker(object):
    def __init__(self,*,host,port):
        self.host = host
        self.port = port
        self.name = "{}_{}".format(self.host,self.port)
        broker_registry[self.name] = self

    def close(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class InMemoryBroker(Broker):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.broker_ctl_q = queue.Queue()
        self.msg_q = queue.Queue()
        self.broker_q = queue.Queue()
        self.exchanges = []
        self.consumer_queues = []

    def close(self):
        self.broker_ctl_q.put("close")

    def run(self):
        while True:
            try:
                broker_ctl_cmd = self.broker_ctl_q.get(timeout=0.001)
            except queue.Empty:
                pass
            else:
                if broker_ctl_cmd == "close":
                    break

            try:
                msg = self.msg_q.get(timeout=0.001)
            except queue.Empty:
                pass
            else:
                self.handle_msg(msg)

    def handle_msg(self, msg):
        try:
            self.command_router(msg)
        except Exception as e:
            tb_str = traceback.format_exc()
            self.put_error(BrokerInternalError,msg=tb_str)

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
        except ExchangeNotFound:
            exch = InMemoryExchange(name=name,type_=type_)
            self.exchanges.append(exch)
        else:
            if type_ != exch.type_:
                msg=("tried to declare an exchange of type {}"
                     " when it has already been declared of typ {}"
                     "").format(type_,exch.type_)

                self.put_error(BadExchange, msg=msg) 


    def put_error(self,e,msg=""):
        self.broker_q.put({ "response": "error",
                            "error": e,
                            "msg": msg
                            })

    def get_exchange(self,name):
        for exch in self.exchanges:
            if exch.name == name:
                return exch

        raise ExchangeNotFound


    def add_consumer_queue(self, name):
        if not self.consumer_queue_exists(name):
            cq = ConsumerQueue(name=name)
            self.consumer_queues.append(cq)

    def get_consumer_queue(self,name):
        for cq in self.consumer_queues:
            if cq.name == name:
                return cq
        
        raise ConsumerQueueNotFound

    def consumer_queue_exists(self,name):
        try:
            self.get_consumer_queue(name)
            return True
        except ConsumerQueueNotFound:
            return False

    def route_message_to_consumer_queues(self,exchange_name,msg,routing_key):
        try:
            exch = self.get_exchange(exchange_name)
        except ExchangeNotFound:
            self.put_error(BadExchange)
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


class RabbitMQBroker(Broker):
    def run(self):
        subprocess.run("sudo systemctl restart rabbitmq.service",shell=True, check=True,timeout=5)
        time.sleep(20)


class Exchange(object):
    def __init__(self,*,name,type_):
        self.name = name
        assert type_ in ["direct","fanout","topic"]
        self.type_ = type_

    def bind(self,queue_name,routing_keys):
        raise NotImplementedError

class InMemoryExchange(Exchange):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.queues = {}

    def bind(self,queue_name,routing_keys):
        if queue_name not in self.queues:
            self.queues[queue_name] = routing_keys
        else:
            self.queues[queue_name].extend(routing_keys)

class ConsumerQueue(object):
    def __init__(self,*,name):
        self.name = name
        self._q = queue.Queue()
        self.callback = None

    def get_next_message(self):
        try:
            msg_dict = self._q.get(timeout=.05)
            return msg_dict
        except queue.Empty:
            raise ConsumeTimeout

    def put(self,data):
        self._q.put(data)

class Connection(object):
    def __init__(self,*,host,port):
        self.host = host
        self.port = port
        self.connect()
        self.connected = True
        self.channel_resources = []

    def create_channel(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def process_events(self,num_cycles=None):
        raise NotImplementedError

    def get_broker(self,*,host,port):
        broker_name = "{}_{}".format(host,port)
        return broker_registry[broker_name]

class InMemoryConnection(Connection):
    def connect(self):
        self.broker = self.get_broker(host=self.host, port=self.port)
        self.msg_q = self.broker.msg_q
        self.broker_q = self.broker.broker_q
    
    def create_channel(self):
        return InMemoryChannelInternal(msg_q=self.msg_q,broker_q=self.broker_q)

    def close(self):
        self.connected = False

    def process_events(self,num_cycles=None):
        while True:
            for chan_resource in self.channel_resources:
                with chan_resource.access() as chan:
                    for queue_name,callback in chan.callbacks.items():
                        cq = self.broker.get_consumer_queue(queue_name)

                        try:
                            msg_dict = cq.get_next_message()
                        except ConsumeTimeout:
                            pass
                        else:
                            callback(msg_dict)

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break

class RabbitMQConnection(Connection):
    def connect(self):
        cp = pika.ConnectionParameters(host=self.host, port=self.port)
        self._conn = pika.BlockingConnection(cp)

    def create_channel(self):
        return self._conn.channel()

    def close(self):
        raise NotImplementedError

    def process_events(self,num_cycles=None):
        while True:
            self._conn.process_data_events(time_limit=0.5)
            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break

class Channel(object):
    def __init__(self,*,conn_resource):
        self.conn_resource = conn_resource
        self.connected = True
        self.connect()

    def connect(self):
        with self.conn_resource.access() as conn:
            self._chan = conn.create_channel()

    def register_producer(self, *, exchange_name, exchange_type):
        raise NotImplementedError

    def register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys):
        raise NotImplementedError

    def publish(self,*,exchange_name, msg, routing_key=''):
        raise NotImplementedError


class InMemoryChannel(Channel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.callbacks = {}


    def publish(self,*,exchange_name,msg,routing_key=''):
        self._chan.msg_q.put(
                        {
                        "command":"publish",
                        "exchange_name":exchange_name,
                        "msg":msg,
                        "routing_key":routing_key,
                        }
                      )

        self._handle_broker_responses()


    def register_producer(self, *, exchange_name, exchange_type):
        self._chan.msg_q.put(
                        {
                        "command":"register_producer",
                        "exchange_name":exchange_name,
                        "exchange_type":exchange_type,
                        }
                       )

        self._handle_broker_responses()

    def register_consumer(self, *, exchange_name, exchange_type, 
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
                        }
                       )

        self.callbacks[queue_name] = callback

        self._handle_broker_responses()

    def _handle_broker_responses(self):
        while True:
            try:
                resp = self._chan.broker_q.get(timeout=0.001)
            except queue.Empty:
                break
            else:
                if resp['response'] == "error":
                    raise resp['error'](resp['msg'])



class RabbitMQChannel(Channel):

    def register_producer(self, *, exchange_name, exchange_type):
        self._chan.exchange_declare(exchange=exchange_name,
                                    type=exchange_type)

    def register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys=[""]):
        self._chan.exchange_declare(exchange=exchange_name,
                                    type=exchange_type)

        exclusive = False
        if queue_name is None:
            exclusive = True
            method_frame = self._chan.queue_declare(exclusive=True)
            queue_name = method_frame.method.queue
        else:
            self._chan.queue_declare(queue=queue_name)

        for r in routing_keys:
            self._chan.queue_bind(exchange=exchange_name,
                                  queue = queue_name,
                                  routing_key = r)

        self._chan.basic_consume(callback,
                                 queue = queue_name,
                                 no_ack = True,
                                 exclusive = exclusive,
                                 consumer_tag = None,
                                 arguments = None)




    def publish(self,*,exchange_name, msg, routing_key=''):
        to_send_json = json.dumps(msg)
        self._chan.basic_publish(exchange=exchange_name,
                                 routing_key=routing_key,
                                 properties = None,
                                 body= to_send_json)









class Resource(object):
    '''
    An object that contains a resource that is only 
    allowed to be accessed by one thread at one time

    Like a thread lock, but safer because the resource
    is only ever exposed from inside a context manager,
    which means it is always released.
    '''

    def __init__(self,*,c_func, c_args=(), c_kwargs={} ):
        self.c_func = c_func
        self.c_args = c_args
        self.c_kwargs = c_kwargs
        self.q_req = queue.Queue(maxsize=1)
        self.q_ret = queue.Queue(maxsize=1)

    def _construct(self):
        return self.c_func(*self.c_args, **self.c_kwargs)

    def request(self,timeout):
        try:
            return self.q_req.get(timeout=timeout)
        except queue.Empty:
            raise ResourceNotAvailable

    def return_(self):
        self.q_ret.put(False)

    def close(self):
        self.q_ret.put(True)

    def _make_available(self,resource):
        self.q_req.put(resource)

    def _is_returned(self,*,timeout):
        try:
            return self.q_ret.get(timeout=timeout)
        except queue.Empty:
            raise ReturnTimeout

    def box(self):
        '''
        Coordinates access to the resource.

        Must run in its own thread.

        '''
        resource = self._construct()

        self._make_available(resource)
        while True:
            try:
                close_box = self._is_returned(timeout=0.1)
                if close_box:
                    break
                self._make_available(resource)
            except ReturnTimeout:
                pass

    @contextmanager
    def access(self,timeout=1):
        """
        Context Manager for accessing a resource
        example:
        with resource_obj.access() as r:
            [code block]...

        The resource resides in a 'resource box' thread and
        is only returned when it is not in use by another thread.

        Raises ResourceAccessTimeout if resource cant be retrieved
        within 1 second.
        """

        resource = self.request(timeout)
        
        try:
            yield resource
        finally:
            #only return it if you actually received it,
            self.return_()