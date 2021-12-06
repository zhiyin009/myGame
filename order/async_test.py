#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   async_pust.py
@Time    :   2021/11/27 00:03:19
@Author  :   xiaozy
'''

import ast
import asyncio as aio
import time
from asyncio import futures
from typing import Any, Dict, List, Optional, Tuple

import httpx
from prometheus_client import start_http_server

from order import Order, OrderAioClient, recv_from_strategies

success = 0


async def order_callback(res: Tuple[httpx.Response, float], err: Optional[Tuple[BaseException, str]], ctx: Tuple[OrderAioClient, bytes, float]) -> None:
    if err:
        exc, tb = err
        print(tb)
        print(exc)
        return

    if res:
        response, start_ns = res
        client, order_b, worker_spawn_ns = ctx
        order = ast.literal_eval(order_b.decode('utf-8'))
        print(
            f'response_latency {order["oid"]}: {(time.time_ns()-start_ns)/1000**2} ms')
        client.metrics.response(response, (time.time_ns()-start_ns)/1000**2)

        global success
        success += 1


async def main():
    # http server for prometheus client
    start_http_server(8000)

    # http client for ordering
    client = OrderAioClient(
        base_url='https://dev/', verify=False, http2=True, timeout=2)

    start_ns = time.time_ns()

    requests = client.build_request(recv_from_strategies(995))
    print(f'order_gen: {(time.time_ns()-start_ns) / 1000**2} ms')

    # warming up
    fs = client.orders([requests[0]], order_callback)
    await fs[0]
    await client.join()

    futures = client.orders(requests, order_callback)
    print(f'spawn: {(time.time_ns() - start_ns) / 1000**2} ms')
    # wait for all task pushed into client.worker
    for fu in futures:
        await fu

    # wait until resquests in client.worker finshed
    await client.close()
    print(f'elapsed: {(time.time_ns() - start_ns) / 1000**2} ms')
    print(f'success: {success}')

if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
