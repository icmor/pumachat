#!/usr/bin/env python
from utils import BaseChat, MessageException
from message import Message
from collections import namedtuple
import asyncio
import socket
import logging
import argparse


class Server:

    Room = namedtuple("Room", ["name", "users", "invites"])

    def __init__(self, host, port):
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

                case {"type": "NEW_ROOM", "roomname": str(roomname)}:
                    if roomname not in self.rooms:
                        room = Server.Room(roomname, {handler.username}, set())
                        self.rooms[room.name] = room
                        await handler.send(
                            Message({"type": "INFO",
                                     "message": "success",
                                     "operation": "NEW_ROOM",
                                     "roomname": roomname})
                        )

                    else:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message":
                                     f"El cuarto '{roomname}' ya existe",
                                     "operation": "NEW_ROOM",
                                     "roomname": roomname})
                        )

                case {"type": "INVITE", "roomname": str(roomname),
                      "usernames": list(usernames)}:
                    if roomname not in self.rooms:
                        await handler.send(Message({"type": "WARNING",
                                                    "message":
                                                    f"El cuarto '{roomname}' "
                                                    "no existe",
                                                    "operation": "INVITE",
                                                    "roomname": roomname}))

                    elif (handler.username not in
                          (room := self.rooms[roomname]).users):
                        await handler.send(Message({"type": "WARNING",
                                                    "message":
                                                    "No eres miembro del "
                                                    f"cuarto '{roomname}'",
                                                    "operation": "INVITE",
                                                    "roomname": roomname}))

                    # walrus operator allows leaking, PEP 572 Appendix B
                    elif any([(username := name) not in self.users
                              for name in usernames]):
                        await handler.send(Message({"type": "WARNING",
                                                    "message":
                                                    f"El usuario '{username}' "
                                                    "no existe",
                                                    "operation": "NEW_ROOM",
                                                    "username": username}))

                    else:
                        invite = Message({"type": "INVITATION",
                                          "message": f"{handler.username} te "
                                          f"invita al cuarto '{roomname}'",
                                          "username": handler.username,
                                          "roomname": roomname})
                        for username in usernames:
                            if (username not in room.users
                                    and username not in room.invites):
                                await self.users[username].send(invite)
                                room.invites.add(username)
                        await handler.send(Message({"type": "INFO",
                                                    "message": "success",
                                                    "operation": "INVITE",
                                                    "roomname": roomname}))

                case {"type": "JOIN_ROOM", "roomname": str(roomname)}:
                    if roomname not in self.rooms:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El cuarto "
                                     f"{roomname} no existe",
                                     "operation": "JOIN_ROOM",
                                     "roomname": roomname})
                            )

                    elif (handler.username in
                          (room := self.rooms[roomname]).users):
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El usuario ya se "
                                     f"unió al cuarto {roomname}",
                                     "operation": "JOIN_ROOM",
                                     "roomname": roomname})
                            )

                    elif handler.username not in room.invites:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El usuario no ha "
                                     "sido invitado al cuarto "
                                     f"{roomname}",
                                     "operation": "JOIN_ROOM",
                                     "roomname": roomname})
                            )

                    else:
                        room.invites.discard(handler.username)
                        room.users.add(handler.username)
                        await handler.send(Message({"type": "INFO",
                                                    "message": "success",
                                                    "operation": "JOIN_ROOM",
                                                    "roomname": roomname}))
                        await self.send_to_all(handler.username,
                                               Message({"type": "JOINED_ROOM",
                                                        "roomname": roomname,
                                                        "username":
                                                        handler.username}))

                case {"type": "ROOM_USERS", "roomname": str(roomname)}:
                    if roomname not in self.rooms:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": f"El cuarto '{roomname}' "
                                     " no existe",
                                     "operation": "ROOM_USERS",
                                     "roomname": roomname})
                        )

                    elif (handler.username not in
                          (room := self.rooms[roomname]).users):
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El usuario no se ha "
                                     f"unido al cuarto '{roomname}'",
                                     "operation": "ROOM_USERS",
                                     "roomname": roomname})
                        )

                    else:
                        await handler.send(
                            Message({"type": "ROOM_USER_LIST",
                                     "usernames": list(room.users)})
                        )

                case {"type": "ROOM_MESSAGE", "roomname": str(roomname),
                      "message": str(message)}:
                    if roomname not in self.rooms:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": f"El cuarto '{roomname}' "
                                     " no existe",
                                     "operation": "ROOM_MESSAGE",
                                     "roomname": roomname})
                        )

                    elif (handler.username not in
                          (room := self.rooms[roomname]).users):
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El usuario no se ha "
                                     f"unido al cuarto '{roomname}'",
                                     "operation": "ROOM_MESSAGE",
                                     "roomname": roomname})
                        )

                    else:
                        await self.send_to_room(
                            room, handler.username,
                            Message({"type": "ROOM_MESSAGE_FROM",
                                     "roomname": roomname,
                                     "username": handler.username,
                                     "message": message})
                        )

                case {"type": "LEAVE_ROOM", "roomname": roomname}:
                    if roomname not in self.rooms:
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": f"El cuarto '{roomname}' "
                                     " no existe",
                                     "operation": "LEAVE_ROOM",
                                     "roomname": roomname})
                        )

                    elif (handler.username not in
                          (room := self.rooms[roomname]).users):
                        await handler.send(
                            Message({"type": "WARNING",
                                     "message": "El usuario no se ha "
                                     f"unido al cuarto '{roomname}'",
                                     "operation": "LEAVE_ROOM",
                                     "roomname": roomname})
                        )

                    else:
                        await handler.send(
                            Message({"type": "INFO",
                                     "message": "success",
                                     "operation": "LEAVE_ROOM",
                                     "roomname": roomname})
                        )
                        room.users.discard(handler.username)
                        if not room.users:
                            self.rooms.pop(roomname)
                        else:
                            await self.send_to_room(
                                room, handler.username,
                                Message({"type": "LEFT_ROOM",
                                         "roomname": roomname,
                                         "username": handler.username})
                            )

                case {"type": "DISCONNECT"}:
                    raise asyncio.CancelledError("Disconnect")
                case _:
                    raise MessageException("Bad format: "
                                           + response.__repr__())

    async def send_to_all(self, username, message):
        logging.debug(f"Sending to all:{message.__repr__()}")
        for name, user in self.users.items():
            if name == username:
                continue
            await user.send(message)

    async def send_to_room(self, room, username, message):
        logging.debug(f"Room message from: {username}")
        logging.debug(message.__repr__())
        for name in room.users:
            if name == username:
                continue
            await self.users[name].send(message)

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


async def main(host, port):
    server = Server(host, port)
    await server.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--host", help="host address",
                        default=socket.gethostname())
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("--silent", action="store_true",
                        help="do not show debug info")
    args = parser.parse_args()
    format = "%(levelname)s [%(name)s: %(lineno)d] %(message)s"
    if args.silent:
        logging.basicConfig(level=logging.CRITICAL, format=format)
    else:
        logging.basicConfig(level=logging.DEBUG, format=format)
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("Cerrando el servidor")
