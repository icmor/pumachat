#!/usr/bin/env python
from utils import BaseChat
from message import Message
import asyncio
import socket
import logging


class Server:

    def __init__(self, host=socket.gethostname(), port=8080):
        self.host = host
        self.port = port

    async def run(self):
        server = await asyncio.start_server(self.handle, self.host, self.port)
        logging.info("Serving on:")
        for sock in server.sockets:
            logging.info(sock.getsockname())
        try:
            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            pass

    async def handle(self, reader, writer):
        handler = ClientHandler(reader, writer)
        await self.recv_messages(handler)

    async def recv_messages(self, handler):
        response = await handler.recv()
        match response:
            case {"type": "IDENTIFY", "username": _}:
                await handler.send(
                    Message({"type": "INFO",
                             "message": "success",
                             "operation": "IDENTIFY"})
                )


class ClientHandler(BaseChat):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer


async def main():
    server = Server()
    await server.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING,
                        format='%(levelname)s [%(name)s] %(message)s')
    asyncio.run(main())
