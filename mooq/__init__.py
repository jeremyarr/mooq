
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

from .resource_factory import connection as create_connection_resource
from .resource_factory import channel as create_channel_resource

def one_plus_one():
    return 2