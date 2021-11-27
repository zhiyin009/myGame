#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   exporter.py
@Time    :   2021/11/27 23:40:44
@Author  :   xiaozy
'''


from prometheus_client import Counter, Histogram


class OrderMetrics():
    def __init__(self):
        self.order_counter_succ = Counter(
            'strategy_order_succ', 'HTTP Success', ['method', 'endpoint'])
        self.order_counter_fail = Counter(
            'strategy_order_fail', 'HTTP Failures', ['method', 'endpoint'])
        self.order_counter_total = Counter(
            'strategy_order_total', 'HTTP Total', ['method', 'endpoint'])
        self.order_histogram = Histogram(
            'strategy_order_latency_second', 'Description of histogram'
        )

    def success(self):
        self.order_counter_total.labels('post', '/api/order').inc()
        self.order_counter_succ.labels('post', '/api/order').inc()

    def fail(self):
        self.order_counter_fail.labels('post', '/api/order').inc()
