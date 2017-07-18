.. image:: docs/_static/logo_full2.png

.. image:: http://tactile.com.au/jenkins/buildStatus/icon?job=mooq1
    :target: https://github.com/jeremyarr/mooq

.. image:: https://img.shields.io/pypi/l/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image:: https://tactile.com.au/badge-server/coverage/mooq1
    :target: https://github.com/jeremyarr/mooq

.. image:: https://img.shields.io/pypi/pyversions/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image::  https://img.shields.io/pypi/status/mooq.svg
    :target: https://pypi.python.org/pypi/mooq

.. image:: https://img.shields.io/pypi/implementation/mooq.svg
    :target: https://pypi.python.org/pypi/mooq


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


Creating a connection:

.. code-block:: python

    conn = await mooq.connect(
                host="localhost",
                port=5672, 
                broker="rabbit"
                )

Creating a channel of the connection:

.. code-block:: python

    chan = await conn.create_channel()

Registering a producer:

.. code-block:: python

    await chan.register_producer(
            exchange_name="log",
            exchange_type="direct"
            )

Registering a consumer and associated callback:

.. code-block:: python

    async def yell_it(resp):
        print(resp['msg'].upper())

    await chan.register_consumer( 
            queue_name="my_queue",
            exchange_name="log", 
            exchange_type="direct",
            routing_keys=["greetings","goodbyes"],
            callback = yell_it
            )

Publishing a message:

.. code-block:: python

    await chan.publish(exchange_name="log",
                       msg="Hello World!",
                       routing_key="greetings")


Process messages asynchronously, running associated callbacks:

.. code-block:: python

    loop = asyncio.get_event_loop()
    loop.create_task(conn.process_events())


More at https://mooq.readthedocs.io
----------------------------------------------

Project Links
-------------

- Docs: https://mooq.readthedocs.io/
- Changelog: https://mooq.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/mooq
- Issues: https://github.com/jeremyarr/mooq/issues

License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/jeremyarr/mooq/blob/master/LICENSE>`_ file for more details.
