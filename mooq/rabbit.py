import subprocess
import time
import json
import os
from functools import wraps, partial
import asyncio

import pika

from . import base


class RabbitMQBroker(base.Broker):
    '''
    Control an existing RabbitMQBroker on your machine.

    Useful when performing integration testing of projects that depend on RabbitMQ.
    '''

    def _run(self):
        if os.environ["TEST_DISTRIBUTION"] == "arch":
            subprocess.run("sudo systemctl restart rabbitmq.service", shell=True, check=True, timeout=5)
        elif os.environ["TEST_DISTRIBUTION"] == "ubuntu":
            subprocess.run("sudo service rabbitmq-server restart", shell=True, check=True, timeout=5)
        else:
            raise ValueError("TEST_DISTRIBUTION environmental variable not set to either arch or ubuntu")

    async def run(self, is_running=None):
        '''
        Restarts the RabbitMQ broker using a method derived from the TEST_DISTRIBUTION
        environmental variable.

        :param is_running: A future set to done once the broker is confirmed
            as being running
        :type is_running: future

        If TEST_DISTRIBUTION=="arch", will try to restart rabbitmq using the linux ``systemctl``
        command.

        If TEST_DISTRIBUTION=="ubuntu", will try to restart rabbitmq using the linux ``service``
        command.

        Will wait for 20 seconds after restarting before returning.

        :raises ValueError: if TEST_DISTRIBUTION environmental variable not found

        .. note:: the user who invokes this method will likely require sudo access to the linux commands.
            This can be provided by editing the sudoers file.
        '''

        await self.loop.run_in_executor(None, self._run)
        await asyncio.sleep(20)
        if is_running:
            is_running.set_result(None)


class RabbitMQConnection(base.Connection):
    '''
    Implementation of a connection to a RabbitMQ broker.
    '''
    def __init__(self, **kwargs):
        '''
        :param host: the hostname of the broker you wish to connect to
        :type host: str
        :param port: the port of the broker you wish to connect to
        :type port: int

        .. note:: must call :meth:`RabbitMQConnection.connect` to actually connect to the broker
        '''

        super().__init__(**kwargs)
        self.channel_resource_constructor_func = RabbitMQChannel

    def _connect(self):
        cp = pika.ConnectionParameters(host=self.host, port=self.port)
        self._conn = pika.BlockingConnection(cp)

    async def connect(self):
        '''
        Connect to the RabbitMQ broker
        '''
        await self.loop.run_in_executor(None, self._connect)

    @base.lock_connection
    def _create_channel(self):
        internal_chan = self._conn.channel()

        chan = RabbitMQChannel(internal_chan=internal_chan, loop=self.loop)
        self.channels.append(chan)
        return chan

    async def create_channel(self):
        '''
        create a channel for multiplexing the connection

        :returns: a :class:`RabbitMQChannel` object
        '''
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._create_channel)

    def close(self):
        '''
        Stop processing events and close the connection to the broker

        :raises NotImplementedError:
        '''
        raise NotImplementedError

    def _process_events(self, num_cycles=None):
        while True:
            with self.conn_lock:
                self._conn.process_data_events(time_limit=0.1)

            if num_cycles is not None:
                num_cycles = num_cycles - 1
                if num_cycles == 0:
                    break

    async def process_events(self, num_cycles=None):
        '''
        Receive messages from the RabbitMQ broker and schedule
        associated callback couroutines.

        Should be run as a task in your app and not awaited for.

        :param num_cycles: the number of times to run the
            event processing loop. A value of None
            will cause events to be processed without a cycle limit.
        :type num_cycles: int|None
        '''
        loop = asyncio.get_event_loop()
        func = partial(self._process_events, num_cycles=num_cycles)
        await loop.run_in_executor(None, func)


class RabbitMQChannel(base.Channel):
    '''
    Implementation of a RabbitMQ Channel
    '''

    @base.lock_channel
    def _register_producer(self, *, exchange_name, exchange_type):
        self._chan.exchange_declare(exchange=exchange_name,
                                    type=exchange_type)

    async def register_producer(self, *, exchange_name, exchange_type):
        '''
        Register a producer on the channel by providing information to
        the broker about the exchange the channel is going to use.

        :param exchange_name: name of the exchange
        :type exchange_name: str
        :param exchange_type: Type of the exchange. Accepted values are "direct",
            "topic" or "fanout"
        :type exchange_type: str
        :returns: None
        '''

        loop = asyncio.get_event_loop()
        func = partial(self._register_producer, exchange_name=exchange_name,
                       exchange_type=exchange_type)

        await loop.run_in_executor(None, func)

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
                                  queue=queue_name,
                                  routing_key=r)

        pika_callback = self._wrap_callback(callback)
        self._chan.basic_consume(pika_callback,
                                 queue=queue_name,
                                 no_ack=True,
                                 exclusive=exclusive,
                                 consumer_tag=None,
                                 arguments=None)

    async def register_consumer(self, queue_name=None, routing_keys=[""], *, exchange_name, exchange_type, callback):
        '''
        Register a consumer on the RabbitMQ channel.

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

        loop = asyncio.get_event_loop()
        func = partial(self._register_consumer, exchange_name=exchange_name,
                       exchange_type=exchange_type, queue_name=queue_name,
                       callback=callback, routing_keys=routing_keys)

        await loop.run_in_executor(None, func)

    def _wrap_callback(self, async_callback):
        '''
        Decorator to turn a pika callback running outside the
        main thread into a coroutine running in the main thread
        with simplified arguments.
        '''

        def thread_callback(ch, meth, prop, body):
            def main_loop_callback(ch, meth, prop, body):
                resp = {
                    "msg": json.loads(body),
                }

                return base.create_task(async_callback(resp), self.loop)

            return self.loop.call_soon_threadsafe(main_loop_callback, ch, meth, prop, body)

        return thread_callback

    @base.lock_channel
    def _publish(self, *, exchange_name, msg, routing_key=''):
        to_send_json = json.dumps(msg)
        self._chan.basic_publish(exchange=exchange_name,
                                 routing_key=routing_key,
                                 properties=None,
                                 body=to_send_json)

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
        loop = asyncio.get_event_loop()
        func = partial(self._publish, exchange_name=exchange_name,
                       msg=msg, routing_key=routing_key)

        await loop.run_in_executor(None, func)
