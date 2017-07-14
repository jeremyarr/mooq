import unittest
import threading
import time

import mooq

class TransportTestCase(unittest.TestCase):

    def setUp(self):
        self.threads_to_close = []

    def tearDown(self):
        pass

    def GIVEN_InMemoryBrokerStarted(self,host,port):
        self.broker = mooq.InMemoryBroker(host=host,port=port)
        t = threading.Thread(target=self.broker.run)
        t.start()
        self.threads_to_close.append(self.broker)

    @classmethod
    def GIVEN_RabbitMQBrokerStarted(cls,host,port):
        cls.broker = mooq.RabbitMQBroker(host=host,port=port)
        cls.broker.run()

    def GIVEN_ConnectionResourceCreated(self,host,port,broker_type):
        self.conn = mooq.connect(broker=broker_type,
                                            host=host,
                                            port=port)

    def GIVEN_ChannelResourceCreated(self):
        self.chan = self.conn.create_channel()

    def GIVEN_ProducerRegistered(self,*,exchange_name,exchange_type):
        self.chan.register_producer(exchange_name=exchange_name,
                                    exchange_type=exchange_type)

    def WHEN_ProducerRegistered(self,*args,**kwargs):
        self.GIVEN_ProducerRegistered(*args,**kwargs)


    def GIVEN_MessagePublished(self, *, exchange_name,msg,routing_key):
        self.chan.publish(exchange_name=exchange_name,
                          msg=msg,
                          routing_key=routing_key)
        #wait for broker to receive messages
        time.sleep(0.005)

    def WHEN_MessagePublished(self,*args,**kwargs):
        self.GIVEN_MessagePublished(*args,**kwargs)



    def GIVEN_ConsumerRegistered(self,*,queue_name,exchange_name,exchange_type,
                                 routing_keys,callback):

        self.chan.register_consumer( queue_name=queue_name,
                                exchange_name=exchange_name,
                                exchange_type=exchange_type,
                                routing_keys=routing_keys,
                                callback = callback)
        #wait for broker to receive messages
        time.sleep(0.005)

    def WHEN_ConsumerRegistered(self,*args,**kwargs):
        self.GIVEN_ConsumerRegistered(*args,**kwargs)





    def WHEN_ProcessEventsNTimes(self,n):
        self.conn.process_events(num_cycles=n)

    def WHEN_ProcessEventsOnce(self):
        self.conn.process_events(num_cycles=1)

    def THEN_CallbackIsRun(self,cb,num_times=1):
        self.assertEqual(num_times,cb.call_count)

    def THEN_CallbackIsNotRun(self,cb):
        cb.assert_not_called()

    def THEN_exception_occurs(self,e):
        self.assertRaises(e,self.func_to_check['func'],
                          *self.func_to_check['args'],
                          *self.func_to_check['kwargs'])