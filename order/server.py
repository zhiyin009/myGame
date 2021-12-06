#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   server.py
@Time    :   2021/11/20 00:36:27
@Author  :   xiaozy 
'''

import asyncio

from aiohttp import web


async def handle(request):
    text = '{"status": "ok"}'
    # await asyncio.sleep(0.002)
    return web.Response(text=text)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/api/order', handle),
                web.post('/api/order', handle)])

if __name__ == '__main__':
    web.run_app(app)
