
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

<<<<<<< HEAD
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
=======
Just mooq it
--------------

Consumer:

.. code-block:: python

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
>>>>>>> 122c43b4d8ce688713b5ef78dbf24cd22dcc1405



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

<<<<<<< HEAD
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

=======
Terminal 1:

.. code-block:: bash
    
    $ python consumer.py

.. code-block:: console

    waiting for first event:
    HELLO WORLD!


Terminal 2:

.. code-block:: bash
    
    $ python producer.py

.. code-block:: console

    published!

>>>>>>> 122c43b4d8ce688713b5ef78dbf24cd22dcc1405
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
<<<<<<< HEAD
=======



Get it now
-----------

With pip:
**********

.. code-block:: bash

    $ pip install mooq
>>>>>>> 122c43b4d8ce688713b5ef78dbf24cd22dcc1405























Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
