import unittest
from unittest.mock import Mock
from .unittest_utils import set_test_hang_alarm, clear_test_hang_alarm, close_all_threads
from .unittest_utils import GWTTestCase
import xmlrunner

import threading
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
print("here is {}".format(here))
sys.path.insert(0,os.path.join(here,".."))

import mooq
from . import common


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




# @unittest.skip("skipped")
class DirectBadExchangeTest(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")

    @clear_test_hang_alarm
    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_bad_exchange(self):
        with self.assertRaises(mooq.BadExchange):
            self.WHEN_ProducerRegistered(exchange_name="fake_exch",
                                          exchange_type="fanout")


# @unittest.skip("skipped")
class InMemoryDirectProduceConsumeTest(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")
    @clear_test_hang_alarm
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



class TopicTestCase(common.TransportTestCase):
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
class FanoutTestCase(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()
        self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="fanout")
    @clear_test_hang_alarm
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
class ExchangeDoesntExistTest(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_BrokerStarted("in_memory","localhost",1234)
        self.GIVEN_ConnectionResourceCreated()
        self.GIVEN_ChannelResourceCreated()

    @clear_test_hang_alarm
    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    @close_all_threads
    def test_publish_to_exchange_that_doesnt_exist(self):
        with self.assertRaises(mooq.BadExchange):
            self.WHEN_MessagePublished(exchange_name="fake_exch",
                                        msg="fake_message",
                                        routing_key="fake_routing_key")




if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)