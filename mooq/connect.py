from .in_memory import InMemoryConnection
from .rabbit import RabbitMQConnection


async def connect(host="localhost", port=5672, broker="rabbit"):
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
        conn = InMemoryConnection(host=host, port=port)
    elif broker == "rabbit":
        conn = RabbitMQConnection(host=host, port=port)
    else:
        raise NotImplementedError

    await conn.connect()
    return conn
