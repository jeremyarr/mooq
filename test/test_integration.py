import unittest
import os
import json
import sys
import asyncio

import xmlrunner

import mooq
from test import common
from test.unittest_utils import asyncio_test

# @unittest.skip("skipped")
class RabbitMQDirectProduceConsumeTest(common.TransportTestCase):
    @classmethod
    def setUpClass(cls):
        cls.GIVEN_RabbitMQBrokerStarted("localhost",5672)

    async def async_setUp(self):
        await super().async_setUp()
        await self.GIVEN_ConnectionResourceCreated("localhost",5672,"rabbit")
        await self.GIVEN_ChannelResourceCreated()


    # @unittest.skip("skipped")
    @asyncio_test
    async def test_direct_runs_callback(self):
        await self.GIVEN_ProducerRegistered(exchange_name="fake_direct_exch",
                                      exchange_type="direct")

        await self.GIVEN_ConsumerRegistered(queue_name="fake_direct_consumer_queue",
                                      exchange_name="fake_direct_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.fake_callback)

        await self.GIVEN_MessagePublished(exchange_name="fake_direct_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_message")

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_topic_runs_callback(self):
        await self.GIVEN_ProducerRegistered(exchange_name="fake_topic_exch",
                                      exchange_type="topic")

        await self.GIVEN_ConsumerRegistered(queue_name="fake_topic_consumer_queue",
                                      exchange_name="fake_topic_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.red","ball.*"],
                                      callback = self.fake_callback)

        await self.GIVEN_MessagePublished(exchange_name="fake_topic_exch",
                                    msg="fake_message",
                                    routing_key="apple.red")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_message")

    # @unittest.skip("skipped")
    @asyncio_test
    async def test_fanout_runs_callback(self):
        await self.GIVEN_ProducerRegistered(exchange_name="fake_fanout_exch",
                                      exchange_type="fanout")

        await self.GIVEN_ConsumerRegistered(queue_name="fake_fanout_consumer_queue1",
                                      exchange_name="fake_fanout_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.fake_callback)

        await self.GIVEN_ConsumerRegistered(queue_name="fake_fanout_consumer_queue2",
                                      exchange_name="fake_fanout_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.fake_callback2)

        await self.GIVEN_MessagePublished(exchange_name="fake_fanout_exch",
                                    msg="fake_message",
                                    routing_key="")

        await self.WHEN_ProcessEventsOnce()

        self.THEN_CallbackReceivesMessage("fake_message")
        self.THEN_Callback2ReceivesMessage("fake_message")




if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)