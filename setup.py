from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'mooq', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name='mooq',
    version=about['__version__'],
    packages=['mooq'],
    description="An asyncio compatible library for interacting with a RabbitMQ AMQP broker",
    long_description="An asyncio compatible library for interacting with a RabbitMQ AMQP broker",
    include_package_data=True,
    install_requires=[
        'pika',
    ],
    zip_safe=False,
    author="Jeremy Arr",
    author_email="jeremyarr@gmail.com",
    license="MIT",
    keywords=["amqp",
              "pika",
              "rabbitmq",
             ],
    url="https://github.com/jeremyarr/mooq",
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
    ]
)

