#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   client.py
@Time    :   2021/11/26 22:01:47
@Author  :   xiaozy
'''

from __future__ import annotations

import asyncio as aio
import time
import traceback
from asyncio.futures import Future
from typing import Any, Awaitable, Callable, Coroutine, List, Optional, Tuple

import httpx
from asyncio_pool import AioPool
from h2.exceptions import ProtocolError
from metrics import OrderMetrics

from .data import Order


class OrderAioClient():
    def __init__(self,
                 base_url: str,
                 verify: Optional[bool] = True,
                 http2: Optional[bool] = False,
                 timeout: Optional[int] = 5):
        self.url = base_url
        self.api_order = 'api/order'
        self.verify = verify
        self.http2 = http2
        self.retry = 3
        self.timeout = timeout

        self.metrics = OrderMetrics()

        self.client: Optional[httpx.AsyncClient] = None
        self._worker = AioPool(10000)
        self._conn_cond = aio.Condition()
        self._connect()

    def _connect(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=self.url,
            verify=self.verify,
            http2=self.http2,
            timeout=self.timeout,
        )

    def build_request(self, orders: List[Order]) -> List[httpx.Request]:

        return [self.client.build_request("post", self.api_order, json=order.__dict__) for order in orders]

    async def aorder(self, request: httpx.Request,
                     cb: Callable[[httpx.Response, Tuple[BaseException, str], Tuple[OrderAioClient]], Coroutine[Any, Any, None]]) -> Future[Any]:

        return await self._worker.spawn(self._wrap(request), cb=cb, ctx=(self, request.read(), time.time_ns()))

    def orders(self, requests: List[httpx.Request],
               cb: Callable[[httpx.Response, Tuple[BaseException, str], Tuple[OrderAioClient]], Coroutine[Any, Any, None]]) -> List[Future[Any]]:

        return [self._worker.spawn_n(self._wrap(request), cb=cb, ctx=(self, request.read(), time.time_ns())) for request in requests]

    async def _wrap(self, request: httpx.Request) -> Optional[httpx.Response]:
        for i in range(1, self.retry+1):
            err = None
            try:
                send_ns = time.time_ns()
                resp = await self.client.send(request)
                return resp, send_ns
            # ProtocolError:
            #   Nginx close connection initiative(keepalive_requests)
            except ProtocolError as e:
                err = e
                # print(
                # f'Failed to send order.oid: {order.oid}, with error {e}, retries: {i}')
                if i == self.retry:
                    raise
            except Exception as e:
                err = e
                # print(
                #     f'Failed to send order.oid: {order.oid}, with error {e}, retries: {i}')
                print(traceback.format_exc())
                if i == self.retry:
                    raise
            finally:
                pass
                # if err:
                #     self.metrics.fail()
                # else:
                #     self.metrics.success()

    async def join(self) -> None:
        await self._worker.join()

    async def close(self, force: bool = False) -> None:
        if not force:
            await self.join()
        await self.client.aclose()
