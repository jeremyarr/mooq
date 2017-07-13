
.. image:: _static/logo_full2.png
.. module:: mooq


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


Get it now
-----------

With pip:
**********

.. code-block:: bash

    $ pip install mooq




Just mooq it
--------------

Producer:

.. code-block:: python

    #example consumer in "Just mooq it" section of docs

    # producer.py

    import mooq

    conn_resource = mooq.create_connection_resource(host="localhost",
                                                    port=5672,
                                                    broker="rabbit")

    chan_resource = mooq.create_channel_resource(conn_resource)

    #the channel is only able to be used within the context manager
    #this prevents two threads communicating on the same 
    #channel at the same time.
    with chan_resource.access() as chan:
        chan.register_producer(exchange_name="log",
                               exchange_type="direct")

        chan.publish(exchange_name="log",
                     msg="Hello World!",
                     routing_key="greetings")
        print("published!")

    #resources must be closed after use
    conn_resource.close()
    chan_resource.close()


Consumer:

.. code-block:: python

    #example consumer in "Just mooq it" section of docs

    #consumer.py

    import mooq
    import json
    import signal
    import sys

    def gracefully_exit(signum, frame):
        conn_resource.close()
        chan_resource.close()
        print("\n")
        sys.exit(0)

    #resources for accessing amqp connections and channels in a thread 
    #safe manner
    conn_resource = mooq.create_connection_resource(host="localhost",
                                                    port=5672,
                                                    broker="rabbit")

    chan_resource = mooq.create_channel_resource(conn_resource)
    signal.signal(signal.SIGINT, gracefully_exit)


    #the callback to run
    def yell_it(ch, meth, prop, body):
        msg = json.loads(body)
        print(msg.upper())

    with chan_resource.access() as chan:
        chan.register_consumer( queue_name="my_queue",
                                exchange_name="log",
                                exchange_type="direct",
                                routing_keys=["greetings","goodbyes"],
                                callback = yell_it)


    #wait for events to be received and process them by running
    #associated callbacks
    with conn_resource.access() as conn:
        print("waiting for first event:")
        conn.process_events()
















.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
