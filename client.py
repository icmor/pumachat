#!/usr/bin/env python
from utils import BaseChat, MessageException
from message import Message
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import asyncio
import socket
import logging
import sys


class Client(BaseChat):

    def __init__(self, host=socket.gethostname(), port=8080):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.session = PromptSession()

    async def connect(self):
        self.reader, self.writer = await \
            asyncio.open_connection(self.host, self.port)

    async def run(self):
        try:
            while True:
                await self.connect()
                if not await self.login():
                    with patch_stdout():
                        if (await self.session.prompt_async(
                                "Reintentar login? [y/n] "
                        )).lower() in ["yes", "y"]:
                            continue
                break
            send_task = asyncio.create_task(self.send_messages())
            recv_task = asyncio.create_task(self.recv_messages())
            await asyncio.gather(send_task, recv_task)
        except (OSError, ConnectionRefusedError) as e:
            logging.critical("Error de conexión.")
            logging.exception(e)
        except MessageException as e:
            logging.critical("Respuesta del servidor no reconocida.")
            logging.exception(e)
        except asyncio.CancelledError as e:
            logging.critical("Error inesperado durante la ejecución.")
            logging.exception(e)
        except SystemExit:
            pass
        finally:
            await self.cleanup()

    async def login(self):
        with patch_stdout():
            username = await self.session.prompt_async("Enter your username: ")
        await self.send(Message({"type": "IDENTIFY",
                                 "username": username}))
        response = await self.recv()
        logging.debug(f"Received: {response.__repr__()}")
        match response:
            case {"type": "INFO", "message": "success"}:
                print(f"Login exitoso! Bienvenido {username}")
                return True
            case {"type": "WARNING"}:
                print(response["message"])
                return False
            case _:
                raise MessageException("Expected message type 'WARNING'. Got",
                                       response.__repr__())

    async def send_messages(self):
        while True:
            with patch_stdout():
                msg = await self.session.prompt_async("> ")
            if not msg.startswith("/"):
                await self.send(Message({"type": "PUBLIC_MESSAGE",
                                         "message": msg}))
            else:
                logging.debug(f"Matching on: {msg.split()}")
                match msg.split():
                    case ["/message"] | ["/message", _]:
                        print("Uso: /message USERNAME MESSAGE\n")

                    case [("/message" | "/MESSAGE"), username, *message]:
                        msg = msg[msg.find(message[0]):]
                        await self.send(Message({"type": "MESSAGE",
                                                 "username": username,
                                                 "message": msg}))

                    case [("/room_message" | "/ROOM_MESSAGE"), _]:
                        print("Usage: /room_message ROOM ...MESSAGE...")

                    case [("/room_message" | "/ROOM_MESSAGE"),
                          roomname, *message]:
                        msg = msg[msg.find(message[0]):]
                        await self.send(Message({"type": "ROOM_MESSAGE",
                                                 "roomname": roomname,
                                                 "message": msg}))

                    case ([("/invite" | "/INVITE")]
                          | [("/invite" | "/INVITE"), _]):
                        print("Uso: /invite ROOMNAME USER1 [USERS...]\n")

                    case [("/invite" | "/INVITE"), roomname, *usernames]:
                        await self.send(Message({"type": "INVITE",
                                                 "roomname": roomname,
                                                 "usernames": usernames}))

                    case [("/status" | "/STATUS"), ("away" | "AWAY"
                                                    | "active" | "ACTIVE"
                                                    | "busy" | "BUSY")
                          as status]:
                        await self.send(Message({"type": "STATUS",
                                                 "status": status.upper()}))

                    case [("/status" | "/STATUS"), *_]:
                        print("Uso: /status (away | active | busy) \n")

                    case [("/users" | "/USERS")]:
                        await self.send(Message({"type": "USERS"}))

                    case [("/users" | "/USERS"), *_]:
                        print("Uso: /users\n")

                    case [("/new_room" | "/NEW_ROOM"), roomname]:
                        await self.send(Message({"type": "NEW_ROOM",
                                                 "roomname": roomname}))

                    case [("/new_room" | "/NEW_ROOM"), *_]:
                        print("Uso: /new_room ROOM\n")

                    case [("/join_room" | "/JOIN_ROOM"), roomname]:
                        await self.send(Message({"type": "JOIN_ROOM",
                                                 "roomname": roomname}))

                    case [("/join_room" | "/JOIN_ROOM"), *_]:
                        print("Uso: /join_room ROOM\n")

                    case [("/room_users" | "/ROOM_USERS"), room]:
                        await self.send(Message({"type": "ROOM_USERS",
                                                 "roomname": room}))

                    case [("/room_users" | "/ROOM_USERS"), *_]:
                        print("Uso: /room_users\n")

                    case [("/leave_room" | "/LEAVE_ROOM"), room]:
                        await self.send(Message({"type": "LEAVE_ROOM",
                                                 "roomname": room}))

                    case [("/leave_room" | "/LEAVE_ROOM"), *_]:
                        print("Uso: /leave_room\n")

                    case [("/disconnect" | "/DISCONNECT")]:
                        await self.send(Message({"type": "DISCONNECT"}))
                        sys.exit(0)

                    case [("/disconnect" | "/DISCONNECT"), *_]:
                        print("Uso: /disconnect\n")

                    case _:
                        print("Comandos: /status, /users, /message, "
                              "/new_room, /invite, /join_room, /room_users"
                              "/room_message, /leave_room, /disconnect\n")

    async def recv_messages(self):
        while True:
            response = await self.recv()
            logging.debug(f"Received: {response.__repr__()}")
            match response:
                case {"type": "NEW_USER", "username": username}:
                    print(f"*{username} se conectó*")

                case {"type": "NEW_STATUS", "username": username,
                      "status": status}:
                    print(f"*{username} cambio su estado a {status}*")

                case {"type": "USER_LIST", "usernames": usernames}:
                    print(f"*Usuarios conectados: {', '.join(usernames)}*")

                case {"type": "MESSAGE_FROM", "username": username,
                      "message": message}:
                    print(f"(privado) {username}: {message}")

                case {"type": "PUBLIC_MESSAGE_FROM", "username": username,
                      "message": message}:
                    print(f"{username}: {message}")

                case {"type": "JOINED_ROOM", "roomname": roomname,
                      "username": username}:
                    print(f"*{username} se unió a {roomname}*")

                case {"type": "ROOM_USER_LIST", "usernames": usernames}:
                    print(f"*Usuarios en {roomname}: {', '.join(usernames)}*")

                case {"type": "ROOM_MESSAGE_FROM", "roomname": roomname,
                      "username": username, "message": message}:
                    print(f"({roomname}) {username}: {message}")

                case {"type": "INVITATION", "username": _,
                      "roomname": _, "message": message}:
                    print(f"*{message}*")

                case {"type": "LEFT_ROOM", "roomname": roomname,
                      "username": username}:
                    print(f"*{username} abandonó {roomname}*")

                case {"type": "DISCONNECTED", "username": username}:
                    print(f"*{username} se desconectó*")

                case {"type": "INFO", "operation": "STATUS",
                      "message": "success"}:
                    print("*Cambio de estado exitoso*")

                case {"type": "INFO", "operation": "NEW_ROOM",
                      "roomname": roomname, "message": "success"}:
                    print(f"*Se creó el cuarto {roomname}*")

                case {"type": "INFO", "operation": "INVITE",
                      "roomname": roomname, "message": "success"}:
                    print(f"*Invitaciones a {roomname} enviadas*")

                case {"type": "INFO", "operation": "JOIN_ROOM",
                      "roomname": roomname, "message": "success"}:
                    print(f"*Te uniste a {roomname}*")

                case {"type": "INFO", "operation": "LEAVE_ROOM",
                      "roomname": roomname, "message": "success"}:
                    print(f"*Abandonaste el cuarto {roomname}*")

                case {"type": "WARNING", "message": message,
                      "operation": (
                          "STATUS"
                          | "MESSAGE"
                          | "NEW_ROOM"
                          | "INVITE"
                          | "JOIN_ROOM"
                          | "ROOM_USERS"
                          | "ROOM_MESSAGE"
                          | "LEAVE_ROOM"
                      )}:
                    print(f"*{message}*")

                case _:
                    logging.debug("Mensaje no reconocido",
                                  response.__repr__())

    async def cleanup(self):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()


async def main():
    client = Client()
    await client.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s [%(name)s:'
                        ' %(lineno)d] %(message)s')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Cerrando el chat, adiós")
