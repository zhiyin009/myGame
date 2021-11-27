#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   async_pust.py
@Time    :   2021/11/27 00:03:19
@Author  :   xiaozy
'''

import logging
import time
import traceback
from typing import Optional, Tuple, Union

import httpx
from asyncio_pool import AioPool

from order import Order, OrderClient, construct_request_header_and_body

oid = 0


def recv_from_strategies() -> list[Order]:
    global oid
    oid += 1
    return [Order(oid, 'buy', 'apple-2112')]


success = 0


def order_callback(res: Optional[httpx.Response], err: Optional[Tuple[BaseException, str]], ctx: httpx.Client) -> None:
    if err:
        exc, tb = err
        print(exc)
        return

    if res.is_success:
        global success
        success += 1
        # print(success)


def main():
    client = httpx.Client(
        base_url='https://dev/', verify=False, http2=True)

    start_ns = time.time_ns()
    i = 1000
    while i > 0:
        resp = None
        err = None
        exc = None
        tb = None
        try:
            resp = client.post(
                url='api/order', data=construct_request_header_and_body(recv_from_strategies()[0]))
            i -= 1
        except BaseException as e:
            exc = e
            tb = traceback.format_exc()
            err = (exc, tb)
            client.close()
            client = httpx.Client(
                base_url='https://dev/', verify=False, http2=True)
        finally:
            order_callback(resp, err=err, ctx=client)

    print(f'elapsed: {(time.time_ns() - start_ns) / 1000**2} ms')
    print(f'success: {success}')


if __name__ == '__main__':
    main()
