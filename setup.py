"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

from os import path
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='bitpanda-pro-sdk',
    version='0.7.0',
    description='Bitpanda Pro Python SDK',

    long_description='Python reference implementation to easily interact with the web socket api from Bitpanda Pro',
    long_description_content_type='text/markdown',

    url='https://github.com/bitpanda-labs/bitpanda-pro-sdk-py',
    author='Bitpanda',
    author_email='support@bitpanda.com',

    classifiers=[
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: Apache Software License',

        # These classifiers are *not* checked by 'pip install'.
        # See instead 'python_requires' below.
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='bitpanda,api,sdk,trading',
    packages=find_packages(exclude=['examples', 'tests', 'docs']),
    python_requires='>=3.7.0, <4',
    install_requires=['websockets', 'dataclasses-json', 'pylint'],
    project_urls={
        'Bug Reports': 'https://github.com/bitpanda-labs/bitpanda-pro-sdk-py/issues',
        'Source': 'https://github.com/bitpanda-labs/bitpanda-pro-sdk-py',
    },
)
