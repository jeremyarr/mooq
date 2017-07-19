from setuptools import setup
import os
import sys
PY_VER = sys.version_info

if not PY_VER >= (3, 6):
    raise RuntimeError("mooq doesn't support Python earlier than 3.6")

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'mooq', '__version__.py'), 'r') as f:
    exec(f.read(), about)

def read(fname):
    with open(os.path.join(here, fname), 'r') as f:
        return str(f.read().strip())

setup(
    name='mooq',
    version=about['__version__'],
    packages=['mooq'],
    description="An asyncio compatible library for interacting with a RabbitMQ AMQP broker",
    long_description='\n\n'.join((read('README.rst'), read('CHANGELOG.rst'))),
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
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
    ]
)

