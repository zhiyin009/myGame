#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   client.py
@Time    :   2021/11/26 22:01:47
@Author  :   xiaozy
'''

import asyncio as aio
import time
from typing import Any, Awaitable, Callable, Coroutine, List, Optional, Tuple

import httpx
from asyncio_pool import AioPool
from h2.exceptions import ProtocolError
from metrics import OrderMetrics

from .data import Order, construct_request_header_and_body


class OrderAioClient():
    def __init__(self,
                 base_url: str,
                 verify: Optional[bool] = True,
                 http2: Optional[bool] = False):
        self.url = base_url
        self.api_order = 'api/order'
        self.verify = verify
        self.http2 = http2
        self.retry = 3

        self.metrics = OrderMetrics()

        self.client: Optional[httpx.AsyncClient] = None
        self._worker = AioPool(1000)
        self._conn_cond = aio.Condition()
        self._connect()

    @property
    def is_connecting(self) -> bool:
        return self._conn_cond.locked()

    @property
    def is_connected(self) -> bool:
        return all((not self.is_connecting, not self.client.is_closed))

    def _connect(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=self.url,
            verify=self.verify,
            http2=self.http2,
        )

    async def reconnect(self, force: bool = False) -> None:
        if not self.is_connected or force:
            if not self.is_connecting:
                async with self._conn_cond:
                    if not self.client.is_closed:
                        await self.client.aclose()
                    self._connect()
                    self._conn_cond.notify_all()
            else:
                async with self._conn_cond:
                    await self._conn_cond.wait()

    async def order(self, orders: List[Order],
                    cb: Callable[[httpx.Response, Tuple[BaseException, str], Tuple[object]], Coroutine[Any, Any, None]]) -> Awaitable[List[httpx.Response]]:

        start_t = time.time()

        async def wrap(order: Order) -> Optional[Coroutine[Any, Any, httpx.Response]]:
            try_reconnect = False
            for i in range(1, self.retry+1):
                err = None
                try:
                    if (not self.is_connected or try_reconnect) and not self.is_connecting:
                        await self.reconnect(force=True)
                        try_reconnect = False
                    return await self.client.post(self.api_order, data=construct_request_header_and_body(order))
                # ProtocolError:
                #   Nginx close connection initiative(keepalive_requests)
                except ProtocolError as e:
                    err = e
                    print(
                        f'Failed to send order.oid: {order.oid}, with error {e}, retries: {i}')
                    try_reconnect = True
                    if i == self.retry:
                        raise
                except Exception as e:
                    err = e
                    print(
                        f'Failed to send order.oid: {order.oid}, with error {e}, retries: {i}')
                    if i == self.retry:
                        raise
                finally:
                    pass
                    # if err:
                    #     self.metrics.fail()
                    # else:
                    #     self.metrics.success()

        return [await self._worker.spawn_n(wrap(order), cb=cb, ctx=(self, order, start_t)) for order in orders]

    async def join(self) -> None:
        await self._worker.join()

    async def close(self, force: bool = False) -> None:
        if not force:
            await self.join()
        await self.client.aclose()
