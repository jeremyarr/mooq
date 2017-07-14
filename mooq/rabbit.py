import pika
import subprocess
import time
import json
import os
from functools import wraps

from . import base


class RabbitMQBroker(base.Broker):
    def run(self):
        if os.environ["TEST_DISTRIBUTION"] == "arch":
            subprocess.run("sudo systemctl restart rabbitmq.service",shell=True, check=True,timeout=5)
        elif os.environ["TEST_DISTRIBUTION"] == "ubuntu":
            subprocess.run("sudo service rabbitmq-server restart",shell=True, check=True,timeout=5)
        else:
            raise ValueError("TEST_DISTRIBUTION environmental variable not set to either arch or ubuntu")

        time.sleep(20)


class RabbitMQConnection(base.Connection):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.channel_resource_constructor_func = RabbitMQChannel

    def connect(self):
        cp = pika.ConnectionParameters(host=self.host, port=self.port)
        self._conn = pika.BlockingConnection(cp)

    @base.lock_connection
    def create_channel(self):
        internal_chan = self._conn.channel()

        chan = RabbitMQChannel(internal_chan=internal_chan)
        self.channels.append(chan)
        return chan

    def close(self):
        raise NotImplementedError

    def process_events(self,num_cycles=None):
        while True:
            with self.conn_lock:
                self._conn.process_data_events(time_limit=0.1)

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break


class RabbitMQChannel(base.Channel):

    @base.lock_channel
    def register_producer(self, *, exchange_name, exchange_type):
        self._chan.exchange_declare(exchange=exchange_name,
                                    type=exchange_type)

    @base.lock_channel
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

        pika_callback = self.wrap_callback(callback)
        self._chan.basic_consume(pika_callback,
                                 queue = queue_name,
                                 no_ack = True,
                                 exclusive = exclusive,
                                 consumer_tag = None,
                                 arguments = None)

    def wrap_callback(self,func):
        @wraps(func)
        def inner(ch,meth,prop,body):
            resp = {
                     "msg": json.loads(body),
                   }
            return func(resp)

        return inner

    @base.lock_channel
    def publish(self,*,exchange_name, msg, routing_key=''):
        to_send_json = json.dumps(msg)
        self._chan.basic_publish(exchange=exchange_name,
                                 routing_key=routing_key,
                                 properties = None,
                                 body= to_send_json)









