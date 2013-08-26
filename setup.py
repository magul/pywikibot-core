# -*- coding: utf-8  -*-
"""
Installer script for Pywikibot 2.0 framework

(C) Pywikipedia team, 2009-2013

Distributed under the terms of the MIT license.

"""
__version__ = '$Id$'

import sys

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

if sys.version_info[0] != 2:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2")
elif sys.version_info[1] < 6:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2.6 or higher")

setup(
    name='Pywikipediabot',
    version='2.0b1',
    description='Python Wikipedia Bot Framework',
    license='MIT License',
    packages=find_packages(),
    install_requires=[
        'httplib2>=0.6.0'
    ],
    test_suite="tests",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta'
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ]
)

# automatically launch generate_user_files.py

import subprocess
python = sys.executable
python = python.replace("pythonw.exe", "python.exe")  # for Windows
ignore = subprocess.call([python, "generate_user_files.py"])
