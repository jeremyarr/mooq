import unittest
from unittest_utils import close_all_threads
import xmlrunner

import os
import json
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
print("here is {}".format(here))
sys.path.insert(0,os.path.join(here,".."))

import mooq
import common





# @unittest.skip("skipped")
class RabbitMQDirectProduceConsumeTest(common.TransportTestCase):
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