#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    context.py

    Class to hold key value.
    :copyright: (c) 2016 by nkwsqyyzx@gmail.com
    :license: BSD, see LICENSE for more details.
"""


class Context(object):
    def __init__(self):
        object.__setattr__(self, '_dict', {})

    def __getattr__(self, item):
        return self._dict.get(item)

    def __setattr__(self, key, value):
        self._dict[key] = value
