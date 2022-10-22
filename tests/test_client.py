from client import Client
from server import Server
import message
import unittest
import logging
import asyncio
import socket

logging.basicConfig(level=logging.CRITICAL)


class ClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = Server(socket.gethostname(), 8080)
        self.client = Client(socket.gethostname(), 8080)
        self.server_task = asyncio.create_task(self.server.run())
        await self.client.connect()

    async def test_identify(self):
        await self.client.send(
            message.Message({"type": "IDENTIFY", "username": "JaneDoe"})
        )
        msg = await self.client.recv()
        self.assertEqual(msg["message"], "success")

    async def asyncTearDown(self):
        self.server_task.cancel()
