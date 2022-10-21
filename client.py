#!/usr/bin/env python
from utils import BaseChat
from message import Message
import asyncio
import socket
import logging


class Client(BaseChat):

    def __init__(self, host=socket.gethostname(), port=8080):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await \
            asyncio.open_connection(self.host, self.port)

    async def run(self):
        await self.send(
            Message({"type": "IDENTIFY", "username": "jane_doe"})
        )
        return await self.recv()


async def main():
    client = Client()
    await client.connect()
    print(await client.run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING,
                        format='%(levelname)s [%(name)s] %(message)s')
    asyncio.run(main())
