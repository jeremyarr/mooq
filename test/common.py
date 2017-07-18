import unittest
import threading
import time
import asyncio

import mooq

class TransportTestCase(unittest.TestCase):

    def setUp(self):
        self.actual = None
        self.actual2 = None

    def tearDown(self):
        pass


    async def async_setUp(self):
        pass

    async def async_tearDown(self):
        pass

    async def GIVEN_InMemoryBrokerStarted(self,host,port):
        self.broker = mooq.InMemoryBroker(host=host,port=port)
        is_running_fut = self.loop.create_future()
        self.loop.create_task(self.broker.run(is_running_fut))
        await is_running_fut

    @classmethod
    def GIVEN_RabbitMQBrokerStarted(cls,host,port):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_debug(True)

        cls.broker = mooq.RabbitMQBroker(host=host,port=port)

        try:
            loop.run_until_complete(cls.broker.run())
        finally:
            loop.close()
        

    async def GIVEN_ConnectionResourceCreated(self,host,port,broker_type):
        self.conn = await mooq.connect(broker=broker_type,
                                        host=host,
                                        port=port)

    async def GIVEN_ChannelResourceCreated(self):
        self.chan = await self.conn.create_channel()

    async def GIVEN_ProducerRegistered(self,*,exchange_name,exchange_type):
        await self.chan.register_producer(exchange_name=exchange_name,
                                          exchange_type=exchange_type)

    async def WHEN_ProducerRegistered(self,*args,**kwargs):
        await self.GIVEN_ProducerRegistered(*args,**kwargs)


    async def GIVEN_MessagePublished(self, *, exchange_name,msg,routing_key):
        await self.chan.publish(exchange_name=exchange_name,
                              msg=msg,
                              routing_key=routing_key)
        #wait for broker to receive messages
        await asyncio.sleep(0.005)

    async def WHEN_MessagePublished(self,*args,**kwargs):
        await self.GIVEN_MessagePublished(*args,**kwargs)


    async def GIVEN_ConsumerRegistered(self,*,queue_name,exchange_name,exchange_type,
                                 routing_keys,callback):

        await self.chan.register_consumer( queue_name=queue_name,
                                exchange_name=exchange_name,
                                exchange_type=exchange_type,
                                routing_keys=routing_keys,
                                callback = callback)
        #wait for broker to receive messages
        await asyncio.sleep(0.005)

    async def WHEN_ConsumerRegistered(self,*args,**kwargs):
        await self.GIVEN_ConsumerRegistered(*args,**kwargs)



    async def WHEN_ProcessEventsNTimes(self,n):
        await self.conn.process_events(num_cycles=n)

    async def WHEN_ProcessEventsOnce(self):
        await self.conn.process_events(num_cycles=1)

    def THEN_CallbackIsRun(self,cb,num_times=1):
        self.assertEqual(num_times,cb.mock.call_count)

    def THEN_CallbackIsNotRun(self,cb):
        cb.assert_not_called()

    def THEN_exception_occurs(self,e):
        self.assertRaises(e,self.func_to_check['func'],
                          *self.func_to_check['args'],
                          *self.func_to_check['kwargs'])

    def THEN_CallbackReceivesMessage(self,expected_msg):
        self.assertEqual(expected_msg,self.actual)

    def THEN_Callback2ReceivesMessage(self,expected_msg):
        self.assertEqual(expected_msg,self.actual2)

    def THEN_CallbackDoesntReceiveMessage(self):
        self.assertEqual(None,self.actual)

    async def fake_callback(self,resp):
        self.actual = resp['msg']

    async def fake_callback2(self,resp):
        self.actual2 = resp['msg']

    async def CloseBroker(self):
        await self.broker.close()