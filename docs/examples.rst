.. _examples:

Examples
==========

.. contents::
   :local:
   :depth: 1


Direct
--------

hello.py:

- Prints a 'tick' message every second and publishes messages to a RabbitMQ at the same time.

.. literalinclude:: ../examples/hello.py


loud.py:

- Prints a 'tick' message every second and processes messages from RabbitMQ at the same time.

.. literalinclude:: ../examples/loud.py

Terminal 1:

.. code-block:: bash

    $ python hello.py

.. code-block:: console

    tick hello 0
    published!
    tick hello 1
    tick hello 2
    published!
    tick hello 3
    tick hello 4
    tick hello 5
    published!
    tick hello 6


Terminal 2:

.. code-block:: bash

    $ python loud.py

.. code-block:: console

    tick loud 0
    HELLO WORLD!
    tick loud 1
    tick loud 2
    HELLO WORLD!
    tick loud 3
    tick loud 4
    tick loud 5
    HELLO WORLD!
    tick loud 6