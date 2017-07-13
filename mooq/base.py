import threading

from .resource import Resource

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


    def _create_connection_resource(self,conn_class):
        conn_resource = Resource(c_func=conn_class,
                                 c_args=(),
                                 c_kwargs={"host":self.host,"port":self.port}) 
        t = threading.Thread(target=conn_resource.box)
        t.start()
        return conn_resource


    def create_connection_resource(self):
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


class ConsumerQueue(object):
    def __init__(self,*,name):
        self.name = name

    def get_next_message(self):
        raise NotImplementedError

    def put(self,data):
        raise NotImplementedError

class Channel(object):
    def __init__(self,*,conn_resource):
        self.conn_resource = conn_resource
        self.connected = True
        # self.connect()

    def connect(self):
        with self.conn_resource.access() as conn:
            self._chan = conn.create_channel()

    def register_producer(self, *, exchange_name, exchange_type):
        raise NotImplementedError

    def register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys):
        raise NotImplementedError

    def publish(self,*,exchange_name, msg, routing_key=''):
        raise NotImplementedError