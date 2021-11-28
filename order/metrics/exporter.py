#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   exporter.py
@Time    :   2021/11/27 23:40:44
@Author  :   xiaozy
'''


import httpx
from prometheus_client import Counter, Histogram


class OrderMetrics():
    def __init__(self):

        self.order_request_total = Counter(
            'order_request_total', 'HTTP Total', ['method', 'endpoint', 'code'])
        self.order_latency_second = Histogram(
            'order_latency_second', 'Description of histogram'
        )

    def response(self, res: httpx.Response, interval: float):
        self.order_request_total.labels(
            res.request.method, res.request.url, res.status_code).inc()

        self.order_latency_second.observe(interval)
