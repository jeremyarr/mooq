from collections import namedtuple
import queue
from contextlib import contextmanager
import uuid
import traceback
import pika
import json
import re
import subprocess
import time

from .__version__ import __version__
from .resource import Resource, ResourceNotAvailable
from . import base

from .base import ExchangeNotFound, \
                  ConsumerQueueNotFound, \
                  ConsumeTimeout, \
                  NothingToConsume, \
                  BadExchange, \
                  BrokerInternalError

from .in_memory import InMemoryBroker, \
                       InMemoryExchange, \
                       InMemoryConsumerQueue, \
                       InMemoryConnection, \
                       InMemoryChannel \



from .rabbit import RabbitMQBroker, \
                    RabbitMQConnection, \
                    RabbitMQChannel

def one_plus_one():
    return 2