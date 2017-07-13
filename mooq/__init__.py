
from .__version__ import __version__
from .resource import Resource, ResourceNotAvailable
from . import base

from .base import ExchangeNotFound, \
                  ConsumerQueueNotFound, \
                  ConsumeTimeout, \
                  NothingToConsume, \
                  BadExchange, \
                  BrokerInternalError, \
                  create_connection_resource, \
                  create_channel_resource

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