import unittest
from unittest.mock import Mock,patch
from unittest_utils import set_test_hang_alarm, clear_test_hang_alarm, close_all_threads
from unittest_utils import GWTTestCase
import xmlrunner


import inspect
import os
import queue
import threading
from contextlib import closing, contextmanager
import signal
import time
import imp
import json
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
print("here is {}".format(here))
sys.path.insert(0,os.path.join(here,".."))

import mooq

class TestHang(Exception):
    pass

# @unittest.skip("skipped") 
class OnePlusOneTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    # @unittest.skip("skipped")
    def test_one_plus_one(self):
        expected_value = 2
        actual_value = one_plus_one()
        self.assertEqual(expected_value,actual_value)

    # @unittest.skip("skipped")
    def test_one_plus_one_marbl(self):
        expected_value = 2
        actual_value = mooq.one_plus_one()
        self.assertEqual(expected_value,actual_value)


def one_plus_one():
    return 1+1



# @unittest.skip("skipped")
class ResourceAccessTest(GWTTestCase):
    @set_test_hang_alarm
    def setUp(self):
        self.threads_to_close = []

    @clear_test_hang_alarm
    def tearDown(self):
        pass

    # @unittest.skip("skipped")
    @close_all_threads
    def test_resource_accessed_through_context_manager(self):

        def fake_resource_constructor_func(a,b,c=7):
            return [a,b,c]

        r = mooq.Resource(
                            c_func=fake_resource_constructor_func,
                            c_args=(1,2),
                            c_kwargs={"c":99})

        self.GIVEN_resource_box_started(r)
        self.GIVEN_expect("resource retrieved to be",[1,2,99])

        self.WHEN_access_resource_through_context_manager()

        self.THEN_ExpectedActualMatch("resource retrieved")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_resource_accessed_through_context_manager_no_constructor_args_kwargs(self):

        def fake_resource_constructor_func():
            return [99]

        r = mooq.Resource(c_func=fake_resource_constructor_func)

        self.GIVEN_resource_box_started(r)
        self.GIVEN_expect("resource retrieved to be",[99])

        self.WHEN_access_resource_through_context_manager()

        self.THEN_ExpectedActualMatch("resource retrieved")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_resource_accessed_through_context_manager_timeout(self):

        def fake_resource_constructor_func():
            return [99]

        r = mooq.Resource(c_func=fake_resource_constructor_func)

        self.GIVEN_resource_box_started(r)

        self.WHEN_access_of_resource_is_nested()

        self.THEN_exception_occurs(mooq.ResourceNotAvailable)

    def GIVEN_resource_box_started(self, r):
        self.resource_obj = r
        t = threading.Thread(target=self.resource_obj.box)
        t.start()
        self.threads_to_close.append(self.resource_obj)

    def WHEN_access_resource_through_context_manager(self):
        with self.resource_obj.access() as r:
            self.actual = r

    def WHEN_access_of_resource_is_nested(self):
        def func_to_check(self):
            with self.resource_obj.access() as x:
                with self.resource_obj.access(timeout=0.1) as y:
                    pass
        self.func_to_check = {"func":func_to_check,
                              "args":(self,),
                              "kwargs":{}}





class TransportTestCase(unittest.TestCase):
    # @set_test_hang_alarm
    def setUp(self):
        self.threads_to_close = []


    # @clear_test_hang_alarm
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


# @unittest.skip("skipped")
class DirectBadExchangeTest(TransportTestCase):
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_bad_exchange(self):
        with self.assertRaises(mooq.BadExchange):
            self.WHEN_ProducerRegistered(exchange_name="fake_exch",
                                          exchange_type="fanout")


# @unittest.skip("skipped")
class InMemoryDirectProduceConsumeTest(TransportTestCase):
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_callback_is_run(self):
        fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = fake_callback)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        self.WHEN_ProcessEventsNTimes(2)

        self.THEN_CallbackIsRun(fake_callback)

    # @unittest.skip("skipped")
    @close_all_threads
    def test_callback_is_not_run_if_routing_key_mismatch(self):
        fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = fake_callback)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="another_routing_key")

        self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackIsNotRun(fake_callback)


    # @unittest.skip("skipped")
    @close_all_threads
    def test_callback_run_if_multiple_routing_keys(self):
        fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key","fake_routing_key2"],
                                      callback = fake_callback)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key2")

        self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackIsRun(fake_callback)


    # @unittest.skip("skipped")
    @close_all_threads
    def test_callback_run_if_two_exclusive_queues_registered(self):
        fake_callback = Mock()
        fake_callback2 = Mock()

        self.GIVEN_ConsumerRegistered(queue_name = None,
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = fake_callback)

        self.GIVEN_ConsumerRegistered(queue_name = None,
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = fake_callback2)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackIsRun(fake_callback)
        self.THEN_CallbackIsRun(fake_callback2)


    # @unittest.skip("skipped")
    @close_all_threads
    def test_bad_exchange(self):
        fake_callback = Mock()

        with self.assertRaises(mooq.BadExchange):
            self.WHEN_ConsumerRegistered( queue_name="fake_consumer_queue",
                                          exchange_name="fake_exch",
                                          exchange_type="fanout",
                                          routing_keys=["fake_routing_key"],
                                          callback = fake_callback)



class TopicTestCase(TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="topic")

    @clear_test_hang_alarm
    def tearDown(self):
        super().tearDown()



# @unittest.skip("skipped")
class InMemoryTopicBallColourTest(TopicTestCase):
    def setUp(self):
        super().setUp()
        self.fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["ball.*","*.red"],
                                      callback = self.fake_callback)
    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_ball_yellow(self):
        self.GWT_BallColour_RunsCallback("ball.yellow")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_ball_red(self):
        self.GWT_BallColour_RunsCallback("ball.red")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_apple_red(self):
        self.GWT_BallColour_RunsCallback("apple.red")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_apple_yellow(self):
        self.GWT_BallColour_DoesntRunCallback("apple.yellow")

    def GWT_BallColour(self,*,routing_key,callback_run):

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key=routing_key)

        self.WHEN_ProcessEventsOnce()

        if callback_run:
            self.THEN_CallbackIsRun(self.fake_callback)
        else:
            self.THEN_CallbackIsNotRun(self.fake_callback)

    def GWT_BallColour_RunsCallback(self,routing_key):
        self.GWT_BallColour(routing_key=routing_key,callback_run=True)

    def GWT_BallColour_DoesntRunCallback(self,routing_key):
        self.GWT_BallColour(routing_key=routing_key,callback_run=False)


# @unittest.skip("skipped")
class InMemoryTopicAllWildcardsTest(TopicTestCase):
    def setUp(self):
        super().setUp()
        self.fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.*"],
                                      callback = self.fake_callback)
    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_runs_callback(self):
        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="absolutely.everything")

        self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackIsRun(self.fake_callback)


# @unittest.skip("skipped")
class InMemoryTopicRunTwiceTest(TopicTestCase):
    def setUp(self):
        super().setUp()
        self.fake_callback = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.*","ball.red"],
                                      callback = self.fake_callback)
    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_runs_callback_twice(self):
        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="ball.red")

        self.WHEN_ProcessEventsNTimes(3)

        self.THEN_CallbackIsRun(self.fake_callback,num_times=2)

# @unittest.skip("skipped")
class FanoutTestCase(TransportTestCase):
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="fanout")

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_routes_to_all_consumer_queues(self):
        self.fake_callback1 = Mock()
        self.fake_callback2 = Mock()

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue1",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys="",
                                      callback = self.fake_callback1)

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue2",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys="",
                                      callback = self.fake_callback2)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="")

        self.WHEN_ProcessEventsNTimes(1)

        self.THEN_CallbackIsRun(self.fake_callback1)
        self.THEN_CallbackIsRun(self.fake_callback2)


# @unittest.skip("skipped")
class ExchangeDoesntExistTest(TransportTestCase):
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_publish_to_exchange_that_doesnt_exist(self):
        with self.assertRaises(mooq.BadExchange):
            self.WHEN_MessagePublished(exchange_name="fake_exch",
                                        msg="fake_message",
                                        routing_key="fake_routing_key")


@unittest.skip("skipped")
class RabbitMQDirectProduceConsumeTest(TransportTestCase):
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("rabbitmq","localhost",5672)
        self.GIVEN_ConnectionResourceCreated(transport_type="rabbitmq", 
                                             host="localhost",
                                             port=5672)
        self.GIVEN_ChannelResourceCreated(transport_type="rabbitmq")
        self.actual = None

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_direct_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.echo_callback1)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_topic_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="topic")

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.red","ball.*"],
                                      callback = self.echo_callback1)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="apple.red")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")

    # @unittest.skip("skipped")
    @close_all_threads
    def test_fanout_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="fanout")

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue1",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.echo_callback1)

        self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue2",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.echo_callback2)

        self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")
        self.THEN_EchoCallback2ReceivesMsg("fake_message")


    def THEN_EchoCallback1ReceivesMsg(self,expected):
        self.assertEqual(expected,self.actual1)

    def THEN_EchoCallback2ReceivesMsg(self,expected):
        self.assertEqual(expected,self.actual1)

    def echo_callback1(self,ch,meth,prop,body):
        msg = json.loads(body)
        self.actual1 = msg

    def echo_callback2(self,ch,meth,prop,body):
        msg = json.loads(body)
        self.actual2 = msg

if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)