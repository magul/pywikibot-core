#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test Editor."""

from __future__ import absolute_import, unicode_literals

import os

import tempfile

from pywikibot import editor


def test_editor_edituserconfigpy_same():
    editor.edit(text=None, jumpIndex=200, highlight='test1')


def test_editor_edituserconfigpy():
    editor.edit(text='test1', jumpIndex=200, highlight='test1')


def test_editor_command():
    tempfile.TemporaryFile(suffix='test', prefix='txt', dir=os.getcwd())
    editor.command(tempFilename=os.getcwd() + 'test.txt', text='test')
