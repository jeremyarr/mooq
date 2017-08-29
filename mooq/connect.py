from .in_memory import InMemoryConnection
from .rabbit import RabbitMQConnection


async def connect(host="localhost", port=5672, broker="rabbit", virtual_host=None):
    '''
    Create a connection object and then connect to a broker

    :param host: the hostname of the broker you wish to connect to
    :type host: str
    :param port: the port of the broker you wish to connect to
    :type port: int
    :param broker: broker type. Currently supported broker types are "rabbit"
        for a RabbitMQ broker and "in_memory" for an broker that resides in memory
        (useful for unit testing)
    :type broker: str
    :return: :class:`InMemoryConnection` or :class:`RabbitMQConnection` object

    .. todo:: raises BrokerConnectionError if cannot connect to the broker

    '''

    if broker == "in_memory":
        conn = InMemoryConnection(host=host, port=port )
    elif broker == "rabbit":
        conn = RabbitMQConnection(host=host, port=port, virtual_host=virtual_host)
    else:
        raise NotImplementedError

    await conn.connect()
    return conn

async def ssl_connect(
            host="localhost", 
            port=5671, 
            broker="rabbit", 
            virtual_host=None,
            ca_certs=None,
            user=None,
            passwd=None):
    '''
    Create a connection object and then connect to a broker

    :param host: the hostname of the broker you wish to connect to
    :type host: str
    :param port: the port of the broker you wish to connect to
    :type port: int
    :param broker: broker type. Currently supported broker types are "rabbit"
        for a RabbitMQ broker and "in_memory" for an broker that resides in memory
        (useful for unit testing)
    :type broker: str
    :return: :class:`InMemoryConnection` or :class:`RabbitMQConnection` object

    .. todo:: raises BrokerConnectionError if cannot connect to the broker

    '''

    conn = RabbitMQConnection(
            host=host, 
            port=port, 
            virtual_host=virtual_host,
            user=user,
            passwd=passwd,
            ca_certs=ca_certs,
            ssl=True)

    await conn.connect()
    return conn
