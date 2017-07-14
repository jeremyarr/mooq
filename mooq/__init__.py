'''
This is a mooq
'''

from .__version__ import __version__

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


def connect(host="localhost",port=5672,broker="rabbit"):
    '''
    create a connection resource
    '''

    if broker == "in_memory":
        return InMemoryConnection(host=host,port=port)
    elif broker == "rabbit":
        return RabbitMQConnection(host=host,port=port)
    else:
        raise NotImplementedError