import unittest
from unittest.mock import Mock
import os
import sys

import xmlrunner

from test import common
from test.unittest_utils import set_test_hang_alarm
from test.unittest_utils import clear_test_hang_alarm
from test.unittest_utils import close_all_threads

import mooq


# @unittest.skip("skipped") 
class InMemoryDirectProduceConsumeTest(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
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




# @unittest.skip("skipped") 
class DirectBadExchangeTest(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
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


class TopicTestCase(common.TransportTestCase):
    @set_test_hang_alarm
    def setUp(self):
        super().setUp()
        self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
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
        self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
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
        self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
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