import pika
import subprocess
import time
import json
import os
from functools import wraps, partial
import asyncio

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

    def _connect(self):
        cp = pika.ConnectionParameters(host=self.host, port=self.port)
        self._conn = pika.BlockingConnection(cp)

    async def connect(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None,self._connect)


    @base.lock_connection
    def _create_channel(self):
        internal_chan = self._conn.channel()

        chan = RabbitMQChannel(internal_chan=internal_chan,loop=self.loop)
        self.channels.append(chan)
        return chan

    async def create_channel(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None,self._create_channel)

    def close(self):
        raise NotImplementedError

    def _process_events(self,num_cycles=None):
        while True:
            with self.conn_lock:
                self._conn.process_data_events(time_limit=0.1)

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break

    async def process_events(self,num_cycles=None):
        loop = asyncio.get_event_loop()
        func = partial(self._process_events, num_cycles=num_cycles)
        await loop.run_in_executor(None,func)


class RabbitMQChannel(base.Channel):

    @base.lock_channel
    def _register_producer(self, *, exchange_name, exchange_type):
        self._chan.exchange_declare(exchange=exchange_name,
                                    type=exchange_type)

    async def register_producer(self, *, exchange_name, exchange_type):
        loop = asyncio.get_event_loop()
        func = partial(self._register_producer,exchange_name=exchange_name,
                       exchange_type=exchange_type)
        
        await loop.run_in_executor(None,func)


    @base.lock_channel
    def _register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys=[""]):
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


    async def register_consumer(self, *, exchange_name, exchange_type, queue_name, callback, routing_keys=[""]):
        loop = asyncio.get_event_loop()
        func = partial(self._register_consumer,exchange_name=exchange_name,
                       exchange_type=exchange_type, queue_name=queue_name,
                       callback=callback, routing_keys=routing_keys)
        
        await loop.run_in_executor(None,func)


    def wrap_callback(self,async_callback):
        def thread_callback(ch,meth,prop,body):
            def main_loop_callback(ch,meth,prop,body):
                resp = {
                         "msg": json.loads(body),
                       }
                return base.create_task(async_callback(resp),self.loop)

            return self.loop.call_soon_threadsafe(main_loop_callback,ch,meth,prop,body)

        return thread_callback

    @base.lock_channel
    def _publish(self,*,exchange_name, msg, routing_key=''):
        to_send_json = json.dumps(msg)
        self._chan.basic_publish(exchange=exchange_name,
                                 routing_key=routing_key,
                                 properties = None,
                                 body= to_send_json)


    async def publish(self,*,exchange_name, msg, routing_key=''):
        loop = asyncio.get_event_loop()
        func = partial(self._publish,exchange_name=exchange_name,
                       msg=msg, routing_key=routing_key)
        
        await loop.run_in_executor(None,func)







