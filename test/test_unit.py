# import unittest
import unittest
from unittest.mock import Mock, MagicMock
import os
import sys
import asyncio

import xmlrunner

from test import common
from test.unittest_utils import set_test_hang_alarm
from test.unittest_utils import clear_test_hang_alarm
from test.unittest_utils import close_all_threads
from test.unittest_utils import asyncio_test, AsyncMock

import mooq




# @unittest.skip("skipped") 
class InMemoryDirectProduceConsumeTest(common.TransportTestCase):
    async def async_setUp(self):
        await self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        await self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
        await self.GIVEN_ChannelResourceCreated()
        await self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                            exchange_type="direct")


    async def async_tearDown(self):
        await self.CloseBroker()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_callback_is_run(self):
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.fake_callback)
        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")
        await self.WHEN_ProcessEventsNTimes(2)

        self.THEN_CallbackReceivesMessage("fake_message")



    # @unittest.skip("skipped")
    @asyncio_test
    async def test_callback_is_not_run_if_routing_key_mismatch(self):
        fake_callback = Mock()
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = fake_callback)

        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="another_routing_key")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackIsNotRun(fake_callback)


    # @unittest.skip("skipped")
    @asyncio_test
    async def test_callback_run_if_multiple_routing_keys(self):
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key","fake_routing_key2"],
                                      callback = self.fake_callback)

        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                        msg="fake_message",
                                        routing_key="fake_routing_key2")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_message")


    # @unittest.skip("skipped")
    @asyncio_test
    async def test_callback_run_if_two_exclusive_queues_registered(self):
        await self.GIVEN_ConsumerRegistered(queue_name = None,
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.fake_callback)

        await self.GIVEN_ConsumerRegistered(queue_name = None,
                                      exchange_name="fake_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.fake_callback2)

        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_message")
        self.THEN_Callback2ReceivesMessage("fake_message")


    # @unittest.skip("skipped")
    @asyncio_test
    async def test_bad_exchange(self):
        fake_callback = Mock()

        with self.assertRaises(mooq.BadExchange):
            await self.WHEN_ConsumerRegistered( queue_name="fake_consumer_queue",
                                          exchange_name="fake_exch",
                                          exchange_type="fanout",
                                          routing_keys=["fake_routing_key"],
                                          callback = fake_callback)




# @unittest.skip("skipped") 
class DirectBadExchangeTest(common.TransportTestCase):
    async def async_setUp(self):
        await self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        await self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
        await self.GIVEN_ChannelResourceCreated()
        await self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="direct")


    async def async_tearDown(self):
        await self.CloseBroker()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_bad_exchange(self):
        with self.assertRaises(mooq.BadExchange):
            await self.WHEN_ProducerRegistered(exchange_name="fake_exch",
                                               exchange_type="fanout")


class TopicTestCase(common.TransportTestCase):

    async def async_setUp(self):
        await self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        await self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
        await self.GIVEN_ChannelResourceCreated()
        await self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="topic")

    async def async_tearDown(self):
        await self.CloseBroker()




# @unittest.skip("skipped") 
class InMemoryTopicBallColourTest(TopicTestCase):
    async def async_setUp(self):
        await super().async_setUp()
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["ball.*","*.red"],
                                      callback = self.fake_callback)
    async def async_tearDown(self):
        await super().async_tearDown()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_ball_yellow(self):
        await self.GWT_BallColour_RunsCallback("ball.yellow")

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_ball_red(self):
        await self.GWT_BallColour_RunsCallback("ball.red")

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_apple_red(self):
        await self.GWT_BallColour_RunsCallback("apple.red")

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_apple_yellow(self):
        await self.GWT_BallColour_DoesntRunCallback("apple.yellow")

    async def GWT_BallColour(self,*,routing_key,callback_run):

        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key=routing_key)

        await self.WHEN_ProcessEventsOnce()

        if callback_run:
            self.THEN_CallbackReceivesMessage("fake_msg")
        else:
            self.THEN_CallbackDoesntReceiveMessage()

    async def GWT_BallColour_RunsCallback(self,routing_key):
        await self.GWT_BallColour(routing_key=routing_key,callback_run=True)

    async def GWT_BallColour_DoesntRunCallback(self,routing_key):
        await self.GWT_BallColour(routing_key=routing_key,callback_run=False)


# @unittest.skip("skipped") 
class InMemoryTopicAllWildcardsTest(TopicTestCase):
    async def async_setUp(self):
        await super().async_setUp()
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.*"],
                                      callback = self.fake_callback)

    async def async_tearDown(self):
        await super().async_tearDown()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_runs_callback(self):
        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="absolutely.everything")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_msg")


# @unittest.skip("skipped") 
class InMemoryTopicRunTwiceTest(TopicTestCase):
    async def async_setUp(self):
        await super().async_setUp()
        self.fake_callback = AsyncMock()
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue",
                                      exchange_name="fake_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.*","ball.red"],
                                      callback = self.fake_callback)


    # @unittest.skip("skipped")
    @asyncio_test
    async def test_runs_callback_twice(self):
        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="ball.red")

        await self.WHEN_ProcessEventsNTimes(3)

        self.THEN_CallbackIsRun(self.fake_callback,num_times=2)

# @unittest.skip("skipped") 
class FanoutTestCase(common.TransportTestCase):
    async def async_setUp(self):
        await super().async_setUp()
        await self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        await self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
        await self.GIVEN_ChannelResourceCreated()
        await self.GIVEN_ProducerRegistered(exchange_name="fake_exch",
                                      exchange_type="fanout")


    async def async_tearDown(self):
        await self.CloseBroker()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_routes_to_all_consumer_queues(self):
        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue1",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys="",
                                      callback = self.fake_callback)

        await self.GIVEN_ConsumerRegistered(queue_name="fake_consumer_queue2",
                                      exchange_name="fake_exch",
                                      exchange_type="fanout",
                                      routing_keys="",
                                      callback = self.fake_callback2)

        await self.GIVEN_MessagePublished(exchange_name="fake_exch",
                                    msg="fake_msg",
                                    routing_key="")

        await self.WHEN_ProcessEventsNTimes(1)

        self.THEN_CallbackReceivesMessage("fake_msg")
        self.THEN_Callback2ReceivesMessage("fake_msg")


# @unittest.skip("skipped") 
class ExchangeDoesntExistTest(common.TransportTestCase):
    async def async_setUp(self):
        await super().async_setUp()
        await self.GIVEN_InMemoryBrokerStarted("localhost",1234)
        await self.GIVEN_ConnectionResourceCreated("localhost",1234,"in_memory")
        await self.GIVEN_ChannelResourceCreated()

    async def async_tearDown(self):
        await self.CloseBroker()

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_publish_to_exchange_that_doesnt_exist(self):
        with self.assertRaises(mooq.BadExchange):
            await self.WHEN_MessagePublished(exchange_name="fake_exch",
                                        msg="fake_message",
                                        routing_key="fake_routing_key")











if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)