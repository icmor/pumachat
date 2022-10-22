#!/usr/bin/env python
from utils import BaseChat, MessageException
from message import Message
import asyncio
import socket
import logging


class Server:

    def __init__(self, host=socket.gethostname(), port=8080):
        self.host = host
        self.port = port
        self.users = {}

    async def run(self):
        server = await asyncio.start_server(self.handle, self.host, self.port)
        logging.info("Serving on:")
        for sock in server.sockets:
            logging.info(sock.getsockname())
        async with server:
            await server.serve_forever()

    async def handle(self, reader, writer):
        handler = ClientHandler(reader, writer)
        try:
            await self.login_user(handler)
            await self.recv_messages(handler)
        except MessageException as e:
            logging.exception(e)
            await handler.send(Message({"type": "ERROR",
                                        "message": str(e)}))
        except asyncio.CancelledError as e:
            logging.debug("Handler cancelado")
            logging.exception(e)

    async def login_user(self, handler):
        msg = await handler.recv()
        logging.debug(f"Received on login: {msg.__repr__()}")
        match msg:
            case {"type": "IDENTIFY", "username": str(username)}:
                if not username:
                    raise asyncio.CancelledError("Login fallido, "
                                                 "usuario inválido")
                elif username not in self.users:
                    handler.username = username
                    self.users[username] = handler
                    await handler.send(
                        Message({"type": "INFO", "message": "success",
                                 "operation": "IDENTIFY"})
                    )
                    # await self.send_to_all(
                        # handler.username,
                        # Message({"type": "NEW_USER",
                                 # "username": handler.username})
                    # )
                else:
                    await handler.send(Message({"type": "WARNING",
                                                "message": "El usuario "
                                                f"{username} ya existe"}))
                    raise asyncio.CancelledError("Login fallido, usuario "
                                                 "ya existe")
            case _:
                raise MessageException("Expected message of type: "
                                       "'IDENTIFY'")

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
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s [%(name)s] %(message)s')
    asyncio.run(main())
