import unittest
import os
import json
import sys

import xmlrunner

import mooq
from test import common

# @unittest.skip("skipped")
class RabbitMQDirectProduceConsumeTest(common.TransportTestCase):
    @classmethod
    def setUpClass(cls):
        cls.GIVEN_RabbitMQBrokerStarted("localhost",5672)

    def setUp(self):
        super().setUp()
        self.GIVEN_ConnectionResourceCreated("localhost",5672,"rabbit")
        self.GIVEN_ChannelResourceCreated()
        self.actual1 = None
        self.actual2 = None

    def tearDown(self):
        super().tearDown()

    # @unittest.skip("skipped")
    def test_direct_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_direct_exch",
                                      exchange_type="direct")

        self.GIVEN_ConsumerRegistered(queue_name="fake_direct_consumer_queue",
                                      exchange_name="fake_direct_exch",
                                      exchange_type="direct",
                                      routing_keys=["fake_routing_key"],
                                      callback = self.echo_callback1)

        self.GIVEN_MessagePublished(exchange_name="fake_direct_exch",
                                    msg="fake_message",
                                    routing_key="fake_routing_key")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")

    # @unittest.skip("skipped")
    def test_topic_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_topic_exch",
                                      exchange_type="topic")

        self.GIVEN_ConsumerRegistered(queue_name="fake_topic_consumer_queue",
                                      exchange_name="fake_topic_exch",
                                      exchange_type="topic",
                                      routing_keys=["*.red","ball.*"],
                                      callback = self.echo_callback1)

        self.GIVEN_MessagePublished(exchange_name="fake_topic_exch",
                                    msg="fake_message",
                                    routing_key="apple.red")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")

    # @unittest.skip("skipped")
    def test_fanout_runs_callback(self):
        self.GIVEN_ProducerRegistered(exchange_name="fake_fanout_exch",
                                      exchange_type="fanout")

        self.GIVEN_ConsumerRegistered(queue_name="fake_fanout_consumer_queue1",
                                      exchange_name="fake_fanout_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.echo_callback1)

        self.GIVEN_ConsumerRegistered(queue_name="fake_fanout_consumer_queue2",
                                      exchange_name="fake_fanout_exch",
                                      exchange_type="fanout",
                                      routing_keys=[""],
                                      callback = self.echo_callback2)

        self.GIVEN_MessagePublished(exchange_name="fake_fanout_exch",
                                    msg="fake_message",
                                    routing_key="")

        self.WHEN_ProcessEventsOnce()

        self.THEN_EchoCallback1ReceivesMsg("fake_message")
        self.THEN_EchoCallback2ReceivesMsg("fake_message")


    def THEN_EchoCallback1ReceivesMsg(self,expected):
        self.assertEqual(expected,self.actual1)

    def THEN_EchoCallback2ReceivesMsg(self,expected):
        self.assertEqual(expected,self.actual2)

    def echo_callback1(self,resp):
        self.actual1 = resp['msg']

    def echo_callback2(self,resp):
        self.actual2 = resp['msg']

if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)