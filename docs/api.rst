.. module:: mooq

API
=====

.. contents::
   :local:
   :depth: 1


Connect to a Broker
---------------------

.. autocofunction:: connect


RabbitMQ Transport
--------------------

.. autoclass:: RabbitMQConnection
    :members:
    :inherited-members:

.. autoclass:: RabbitMQChannel
    :members:
    :inherited-members:

.. autoclass:: RabbitMQBroker
    :members:
    :inherited-members:

In Memory Transport
--------------------

.. autoclass:: InMemoryConnection
    :members:
    :inherited-members:

.. autoclass:: InMemoryChannel
    :members:
    :inherited-members:

.. autoclass:: InMemoryBroker
    :members:
    :inherited-members:


Custom Exceptions
------------------

.. autoexception:: ExchangeNotFound

.. autoexception:: ConsumerQueueNotFound

.. autoexception:: ConsumeTimeout

.. autoexception:: NothingToConsume

.. autoexception:: BadExchange

.. autoexception:: BrokerInternalError