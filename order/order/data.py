#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   order.py
@Time    :   2021/11/26 21:47:28
@Author  :   xiaozy
'''


from typing import List

oid = 0


class Order():
    def __init__(self, oid: int, trade: str, obj: str):
        self.oid = oid
        self.trade = trade
        self.obj = obj


def recv_from_strategies(num: int = 1) -> List[Order]:
    global oid
    res: List[Order] = []
    for _ in range(num):
        oid += 1
        res.append(Order(oid, 'buy', 'apple-2112'))

    return res
