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
from typing import List, Optional, Tuple

import httpx

from order import Order, OrderAioClient, recv_from_strategies

oid = 0

success = 0


def order_callback(res: Tuple[httpx.Response], err: Optional[Tuple[BaseException, str]], ctx: Tuple[OrderAioClient, float]) -> None:
    if err:
        exc, tb = err
        print(tb)
        print(exc)
        return

    if res:
        response = res
        client, send_ns = ctx
        print(f'response: {(time.time_ns()-send_ns) / 1000**2} ms')

        global success
        success += 1


def main():
    # http client for ordering
    client = httpx.Client(
        base_url='https://dev/', verify=False, http2=True, timeout=2)

    start_ns = time.time_ns()

    requests = [client.build_request(
        "post", 'api/order', json=order.__dict__) for order in recv_from_strategies(995)]
    print(f'order_gen: {(time.time_ns()-start_ns) / 1000**2} ms')

    for request in requests:
        resp = None
        err = None
        exc = None
        tb = None
        try:
            send_ns = time.time_ns()
            resp = client.send(request)
        except BaseException as e:
            exc = e
            tb = traceback.format_exc()
            err = (exc, tb)
            client.close()
            client = httpx.Client(
                base_url='https://dev/', verify=False, http2=True)
        else:
            order_callback(resp, err=err, ctx=(client, send_ns))

    print(f'elapsed: {(time.time_ns() - start_ns) / 1000**2} ms')
    print(f'success: {success}')


if __name__ == '__main__':
    main()
