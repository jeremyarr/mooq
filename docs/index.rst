
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

`mooq <https://github.com/jeremyarr/jenkins_badges>`_ is a thread-safe library for interacting with an AMQP broker such as `RabbitMQ <https://www.rabbitmq.com/tutorials/tutorial-one-python.html>`_ in a simple, pythonic way.


Features
----------

- Simplified, pythonic interface to RabbitMQ with sensible defaults
- Interfaces with a `RabbitMQ 0-9-1` broker
- Supports direct, topic and fanout exchange types
- Contains an implementation of an "in memory" broker to assist in unit testing projects that depend on AMQP
- Designed for thread safe use of AMQP connections and channels.

Pika's documentation states you cant rely on connection and channel objects being thread safe


Just mooq it
--------------

Consumer:

.. code-block:: python

#consumer.py

    import mooq

    #the callback to run
    def yell_it(resp):
        print(resp['msg'].upper())

    conn = mooq.connect(host="localhost",
                                  port=5672,
                                  broker="rabbit")
    chan = conn.create_channel()

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
