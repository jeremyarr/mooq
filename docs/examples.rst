Examples
==========

.. contents::
   :local:
   :depth: 1


Direct
--------

Consumer:

- An asyncio app that prints a 'tick' message every second and processes messages from RabbitMQ at the same time.

.. literalinclude:: ../examples/direct_consumer.py


Producer:

- An asyncio app that prints a 'tick' message every second and publishes messages to a RabbitMQ at the same time.

.. literalinclude:: ../examples/direct_consumer.py

Terminal 1:

.. code-block:: bash
    
    $ python direct_consumer.py

.. code-block:: console

    waiting for first event...
    tick consumer app 1
    HELLO WORLD!
    tick consumer app 2
    tick consumer app 3
    tick consumer app 4
    tick consumer app 5
    HELLO WORLD!
    tick consumer app 6


Terminal 2:

.. code-block:: bash
    
    $ python direct_producer.py

.. code-block:: console

    tick producer app 1
    published!
    tick producer app 2
    tick producer app 3
    tick producer app 4
    tick producer app 5
    published!
    tick producer app 6