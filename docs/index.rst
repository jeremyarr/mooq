
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

`mooq <https://github.com/jeremyarr/jenkins_badges>`_ is a asyncio compatible library for interacting with `RabbitMQ <https://www.rabbitmq.com/tutorials/tutorial-one-python.html>`_ AMQP broker.

AM-Rabbit What?
-----------------

AMQP is an international communication standard that specifies how a producer can send messages to one or more consumers in an asynchronous and robust way through a middleman called a broker.

RabbitMQ is a popular implementation of an AMQP (version 0-9-1) broker with client libraries written in a wide variety of programming languages.

AMQP is very useful for communicating between microservices because messages can be passed around asynchronously and flexibly, ensuring microservices are more decoupled. Plus, all the low level communication is taken care of for you.

But Why?
---------

`mooq`:

- is designed for use in asyncio applications.
- provides a simplified and pythonic API to RabbitMQ with sensible defaults
- is built on top of the reliable and proven pika library
- includes an in memory broker option for unit testing projects that depend on AMQP


Just mooq it
--------------

Consumer:

.. code-block:: python

    #consumer.py

    import mooq
    import asyncio

    #the callback to run
    async def yell_it(resp):
        print(resp['msg'].upper())

    async def main(loop):
        conn = await mooq.connect(host="localhost",
                            port=5672,
                            broker="rabbit")
        chan = await conn.create_channel()

        await chan.register_consumer( queue_name="my_queue",
                                exchange_name="log",
                                exchange_type="direct",
                                routing_keys=["greetings","goodbyes"],
                                callback = yell_it)

        loop.create_task(tick_every_second())
        loop.create_task(conn.process_events())


    async def tick_every_second():
        cnt = 0
        while True:
            print("tick consumer app {}".format(cnt))
            cnt = cnt + 1
            await asyncio.sleep(1)

    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()

Producer:

.. code-block:: python

    import mooq
    import asyncio
    import random

    #ideal API

    async def main():
        conn = await mooq.connect(host="localhost",
                                  port=5672,
                                  broker="rabbit")
        chan = await conn.create_channel()

        await chan.register_producer(exchange_name="log",
                                     exchange_type="direct")

        loop.create_task(tick_every_second())
        loop.create_task(publish_randomly(chan))

    async def tick_every_second():
        cnt = 0
        while True:
            print("tick producer app {}".format(cnt))
            cnt = cnt + 1
            await asyncio.sleep(1)

    async def publish_randomly(chan):
        while True:
            await chan.publish(exchange_name="log",
                               msg="Hello World!",
                               routing_key="greetings")
            print("published!")

            await asyncio.sleep(random.randint(1,10))

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()


Terminal 1:


.. code-block:: bash
    
    $ python consumer.py

.. code-block:: console

    waiting for first event...
    tick producer app 1
    HELLO WORLD!
    tick producer app 2
    tick producer app 3
    tick producer app 4
    tick producer app 5
    HELLO WORLD!
    tick producer app 6


Terminal 2:

.. code-block:: bash
    
    $ python producer.py

.. code-block:: console

    tick producer app 1
    published!
    tick producer app 2
    tick producer app 3
    tick producer app 4
    tick producer app 5
    published!
    tick producer app 6



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
