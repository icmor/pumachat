import message


class BaseChat:
    async def send(self, message):
        self.writer.write(message.encoded)
        await self.writer.drain()

    async def recv(self):
        data = await self.reader.readuntil(b"}")
        return message.Message.from_encoded(data.lstrip(b"\x00\n"))


class MessageException(Exception):
    pass
