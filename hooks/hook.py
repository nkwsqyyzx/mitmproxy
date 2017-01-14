#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    hook.py

    A Simple HTTP Hook Proxy Server in Python.
    :copyright: (c) 2016 by nkwsqyyzx@gmail.com
    :license: BSD, see LICENSE for more details.
"""

# import from your own hooks to replace next line
HOOKS = []

def request(flow):
    for hook in HOOKS:
        if hook.host_check(flow) and hook.respond(flow):
            hook.rewrite_client_request(flow)


def response(flow):
    for hook in HOOKS:
        if hook.host_check(flow) and hook.respond(flow):
            hook.rewrite_server_response(flow)


