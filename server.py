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
        except asyncio.exceptions.IncompleteReadError:
            logging.debug("Client disconnected")
        finally:
            await self.cleanup(handler)

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
                    await self.send_to_all(
                        handler.username,
                        Message({"type": "NEW_USER",
                                 "username": handler.username})
                    )
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
        while True:
            response = await handler.recv()
            match response:
                case {"type": "STATUS",
                      "status": ("AWAY" | "ACTIVE" | "BUSY") as status}:
                    if status == handler.status:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": f"El estado ya es {status}",
                                     "operation": "STATUS",
                                     "status": status})
                        )
                    else:
                        handler.status = status
                        await handler.send(
                            Message({"type": "INFO",
                                     "message": "success",
                                     "operation": "STATUS"})
                        )
                        await self.send_to_all(
                            handler.username,
                            Message({"type": "NEW_STATUS",
                                     "username": handler.username,
                                     "status": status})
                        )

                case {"type": "USERS"}:
                    await handler.send(
                        Message({"type": "USER_LIST",
                                 "usernames": list(self.users.keys())})
                    )

                case {"type": "MESSAGE", "username": str(username),
                      "message": str(message)}:
                    if username == handler.username:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "operation": "MESSAGE",
                                     "message":
                                     "No puedes mandarte mensajes a tí mismo"})
                        )

                    elif username not in self.users:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "operation": "MESSAGE",
                                     "message":
                                     f"El usuario {username} no existe"})
                        )

                    else:
                        await self.send_private_message(
                            handler.username, username,
                            Message({"type": "MESSAGE_FROM",
                                     "username": handler.username,
                                     "message": message})
                        )

                case {"type": "PUBLIC_MESSAGE", "message": str(message)}:
                    await self.send_to_all(
                        handler.username,
                        Message({"type": "PUBLIC_MESSAGE_FROM",
                                 "username": handler.username,
                                 "message": message})
                    )

                case {"type": "DISCONNECT"}:
                    raise asyncio.CancelledError("Disconnect")
                case _:
                    raise MessageException(f"Bad format: {response.__repr__()}")

    async def send_to_all(self, username, message):
        logging.debug(f"Sending to all:{message.__repr__()}")
        for name, user in self.users.items():
            if name == username:
                continue
            await user.send(message)

    async def send_private_message(self, username, receiver, message):
        logging.debug(f"Private message: {username} -> {receiver}")
        logging.debug(message.__repr__())
        await self.users[receiver].send(message)


    async def cleanup(handler):
        pass

class ClientHandler(BaseChat):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.username = None
        self.status = "ACTIVE"

async def main():
    server = Server()
    await server.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s [%(name)s] %(message)s')
    asyncio.run(main())
