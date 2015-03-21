from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='snmp2canopsis',
    version='0.1',
    description='Send SNMP trap to Canopsis/AMQP',
    long_description=long_description,
    author='Mathieu Virbel',
    author_email='mat@meltingrocks.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=["kombu", "pysnmp", "Logbook"],
    packages=["snmp2canopsis"],
    entry_points={
        'console_scripts': [
            'snmp2canopsis=snmp2canopsis.snmp2canopsis:main',
            'cat-snmp2canopsis=snmp2canopsis.manage:main'
        ],
    },
)
