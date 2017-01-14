#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    ReadWriteHook.py

    A Simple HTTP Hook Proxy Server in Python.
    :copyright: (c) 2016 by nkwsqyyzx@gmail.com
    :license: BSD, see LICENSE for more details.
"""


class ReadWriteHook(object):
    def host_check(self, flow):
        """:host to hook"""
        raise NotImplementedError()

    def rewrite_client_request(self, flow):
        """:modify client request"""
        raise NotImplementedError()

    def rewrite_server_response(self, flow):
        """:modify server response"""
        raise NotImplementedError()

    def respond(self, flow):
        """:return True to enable hook"""
        raise NotImplementedError()



