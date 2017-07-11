import pika
import subprocess
import time
import json

from . import base

class RabbitMQBroker(base.Broker):
    def run(self):
        subprocess.run("sudo systemctl restart rabbitmq.service",shell=True, check=True,timeout=5)
        time.sleep(20)

class RabbitMQConnection(base.Connection):
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


class RabbitMQChannel(base.Channel):

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









