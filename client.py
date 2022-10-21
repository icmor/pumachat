#!/usr/bin/env python
from utils import BaseChat, MessageException
from message import Message
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import asyncio
import socket
import logging


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
        finally:
            await self.cleanup()

    async def login(self):
        with patch_stdout():
            username = await self.session.prompt_async("Enter your username: ")
        await self.send(Message({"type": "IDENTIFY",
                                 "username": username}))
        response = await self.recv()
        logging.debug(response.__repr__())
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
                match msg.split():
                    case [("/message" | "/MESSAGE"), username, *message]:
                        msg = msg[msg.find(message[0]):]
                        logging.debug("Sending message", msg.__repr__())
                        await self.send(Message({"type": "MESSAGE",
                                                 "username": username,
                                                 "message": msg}))

                    case _:
                        print("Comandos: /message, /public_message\n")

    async def recv_messages(self):
        while True:
            response = await self.recv()
            logging.debug(response.__repr__())
            match response:
                case {"type": "MESSAGE_FROM", "username": username,
                      "message": message}:
                    print(f"(privado) {username}: {message}")

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
        print("Cerrando el chat, adiós")
