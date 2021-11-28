#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   order.py
@Time    :   2021/11/26 21:47:28
@Author  :   xiaozy
'''


from typing import Any, Dict


class Order():
    def __init__(self, oid: int, trade: str, obj: str):
        self.oid = oid
        self.trade = trade
        self.obj = obj


def construct_request_header_and_body(order: Order) -> Dict[str, Any]:
    return order.__dict__
