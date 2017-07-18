
.. image:: _static/logo_full2.png


Welcome to mooq
=================

.. image:: https://img.shields.io/pypi/v/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image:: https://img.shields.io/pypi/l/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image:: https://img.shields.io/pypi/pyversions/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image::  https://img.shields.io/pypi/status/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image:: https://img.shields.io/pypi/implementation/mooq.svg
    :target: https://pypi.python.org/pypi/mooq


Latest Version: v |version|

`mooq <https://github.com/jeremyarr/mooq>`_ is an asyncio compatible library for interacting with a `RabbitMQ <https://www.rabbitmq.com>`_ AMQP broker.

Features
---------

- Uses asyncio. No more callback hell.
- Simplified and pythonic API to RabbitMQ
- Built on top of the proven `pika <https://github.com/pika/pika>`_ library
- Comes with an in memory broker for unit testing projects that depend on RabbitMQ

Get It Now
-----------

.. code-block:: bash

    $ pip install mooq

Just mooq it
--------------

Just some of the ways to use `mooq`:


Creating a connection::

    conn = await mooq.connect(
                host="localhost",
                port=5672, 
                broker="rabbit"
                )

Creating a channel of the connection::

    chan = await conn.create_channel()

Registering a producer::

    await chan.register_producer(
            exchange_name="log",
            exchange_type="direct"
            )

Registering a consumer and associated callback::

    async def yell_it(resp):
        print(resp['msg'].upper())

    await chan.register_consumer( 
            queue_name="my_queue",
            exchange_name="log", 
            exchange_type="direct",
            routing_keys=["greetings","goodbyes"],
            callback = yell_it
            )

Publishing a message::

    await chan.publish(exchange_name="log",
                       msg="Hello World!",
                       routing_key="greetings")


Process messages asynchronously, running associated callbacks::

    loop = asyncio.get_event_loop()
    loop.create_task(conn.process_events())





User Guide
-----------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   installation
   quickstart
   advanced_usage
   unit_testing
   examples
   api
   changelog
   license
   authors
   kudos
























Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
