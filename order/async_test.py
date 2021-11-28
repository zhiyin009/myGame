#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   async_pust.py
@Time    :   2021/11/27 00:03:19
@Author  :   xiaozy
'''

import asyncio as aio
import logging
import time
from typing import Callable, List, Optional, Tuple

import httpx
from prometheus_client import start_http_server

from order import Order, OrderAioClient
from order.aclient import OrderAioClient

oid = 0


def recv_from_strategies() -> List[Order]:
    global oid
    oid += 1
    return [Order(oid, 'buy', 'apple-2112')]


success = 0


async def order_callback(res: Optional[httpx.Response], err: Optional[Tuple[BaseException, str]], ctx: Tuple[object]) -> None:
    if err:
        exc, tb = err
        print(tb)
        print(exc)
        return

    if res and res.is_success:
        global success
        success += 1
        # print(success)


async def main():
    # http server for prometheus client
    start_http_server(8000)

    # http client for ordering
    client = OrderAioClient(
        base_url='https://dev/', verify=False, http2=True)

    start_ns = time.time_ns()
    if client.is_connected:
        futures = [client.order(recv_from_strategies(), order_callback)
                   for _ in range(100000)]

        # wait for all task pushed into client.worker
        for fu in futures:
            await fu

        # wait for all task in worker being finished

    await client.close()

    print(f'elapsed: {(time.time_ns() - start_ns) / 1000**2} ms')
    print(f'success: {success}')

if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
