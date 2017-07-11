import unittest
import threading
import time


import mooq

class TransportTestCase(unittest.TestCase):
    def setUp(self):
        self.threads_to_close = []

    def tearDown(self):
        pass

    def GIVEN_BrokerStarted(self,type_,host,port):
        if type_ == "in_memory":
            self.broker = mooq.InMemoryBroker(host="blah",port=1234)
            t = threading.Thread(target=self.broker.run)
            t.start()
            self.threads_to_close.append(self.broker)
        elif type_ == "rabbitmq":
            self.broker = mooq.RabbitMQBroker(host="blah",port=1234)
            self.broker.run()
        else:
            raise NotImplementedError

    def GIVEN_ProducerRegistered(self,*,exchange_name,exchange_type):
        with self.chan_resource.access() as chan:
            chan.register_producer(exchange_name=exchange_name,
                                   exchange_type=exchange_type)

    def WHEN_ProducerRegistered(self,*args,**kwargs):
        self.GIVEN_ProducerRegistered(*args,**kwargs)

    def GIVEN_ConsumerRegistered(self,*,queue_name,exchange_name,exchange_type,
                                 routing_keys,callback):

        with self.chan_resource.access() as chan:
            chan.register_consumer( queue_name=queue_name,
                                    exchange_name=exchange_name,
                                    exchange_type=exchange_type,
                                    routing_keys=routing_keys,
                                    callback = callback)
        #wait for broker to receive messages
        time.sleep(0.005)

    def WHEN_ConsumerRegistered(self,*args,**kwargs):
        self.GIVEN_ConsumerRegistered(*args,**kwargs)

    def GIVEN_ConnectionResourceCreated(self,transport_type="in_memory",host="blah",port=1234):
        if transport_type == "in_memory":
            c_func = mooq.InMemoryConnection
        elif transport_type == "rabbitmq":
            c_func = mooq.RabbitMQConnection
        else:
            raise NotImplementedError

        self.conn_resource = mooq.Resource(c_func=c_func,
                                                c_args=(),
                                                c_kwargs={"host":host,"port":port}) 
        t = threading.Thread(target=self.conn_resource.box)
        t.start()

        self.threads_to_close.append(self.conn_resource)

    def GIVEN_ChannelResourceCreated(self,transport_type="in_memory"):
        if transport_type == "in_memory":
            c_func = mooq.InMemoryChannel
        elif transport_type == "rabbitmq":
            c_func = mooq.RabbitMQChannel
        else:
            raise NotImplementedError

        self.chan_resource = mooq.Resource(c_func=c_func,
                                                c_args=(),
                                                c_kwargs={"conn_resource":self.conn_resource}) 

        t = threading.Thread(target=self.chan_resource.box)
        t.start()

        self.threads_to_close.append(self.chan_resource)
        with self.conn_resource.access() as conn:
            conn.channel_resources.append(self.chan_resource)


    def GIVEN_MessagePublished(self, *, exchange_name,msg,routing_key):
        with self.chan_resource.access() as chan:
            chan.publish(exchange_name=exchange_name,
                         msg=msg,
                         routing_key=routing_key)
        #wait for broker to receive messages
        time.sleep(0.005)

    def WHEN_MessagePublished(self,*args,**kwargs):
        self.GIVEN_MessagePublished(*args,**kwargs)

    def WHEN_ProcessEventsNTimes(self,n):
        with self.conn_resource.access() as conn:
            conn.process_events(num_cycles=n)

    def WHEN_ProcessEventsOnce(self):
        with self.conn_resource.access() as conn:
            conn.process_events(num_cycles=1)

    def THEN_CallbackIsRun(self,cb,num_times=1):
        self.assertEqual(num_times,cb.call_count)

    def THEN_CallbackIsNotRun(self,cb):
        cb.assert_not_called()

    def THEN_exception_occurs(self,e):
        self.assertRaises(e,self.func_to_check['func'],
                          *self.func_to_check['args'],
                          *self.func_to_check['kwargs'])