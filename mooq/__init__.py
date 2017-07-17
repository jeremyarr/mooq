'''
This is a mooq
'''

import asyncio

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


async def connect(host="localhost",port=5672,broker="rabbit"):
    '''
    create a connection resource
    '''

    if broker == "in_memory":
        conn = InMemoryConnection(host=host,port=port)
    elif broker == "rabbit":
        conn = RabbitMQConnection(host=host,port=port)
    else:
        raise NotImplementedError

    await conn.connect()
    return conn