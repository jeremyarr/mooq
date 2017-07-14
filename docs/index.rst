
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

AMQP is an international standard that specifies how a producer can send messages to one or more consumers in an asynchronous and robust way through a middleman called a broker.

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

    #the callback to run
    def yell_it(resp):
        print(resp['msg'].upper())


    #connection and channel objects can be safely 
    #used in different threads!

    conn = mooq.connect(host="localhost",
                                  port=5672,
                                  broker="rabbit")
    chan = conn.create_channel()

    #takes care of boring AMQP stuff behind the scenes
    chan.register_consumer( queue_name="my_queue",
                            exchange_name="log",
                            exchange_type="direct",
                            routing_keys=["greetings","goodbyes"],
                            callback = yell_it)

    #blocking
    print("waiting for first event...")
    conn.process_events()

Producer:

.. code-block:: python

    # producer.py

    import mooq


    #connection and channel objects can be safely 
    #used in different threads!

    conn = mooq.connect(host="localhost",
                                  port=5672,
                                  broker="rabbit")
    chan = conn.create_channel()

    chan.register_producer(exchange_name="log",
                           exchange_type="direct")

    chan.publish(exchange_name="log",
                 msg="Hello World!",
                 routing_key="greetings")

    print("published!")


Terminal 1:


.. code-block:: bash
    
    $ python consumer.py

.. code-block:: console

    waiting for first event...
    HELLO WORLD!


Terminal 2:

.. code-block:: bash
    
    $ python producer.py

.. code-block:: console

    published!




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
