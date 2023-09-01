import argparse
import asyncio

LIMIT = 2 ** 16


async def stream_copy(reader, writer):
    try:
        while not reader.at_eof():
            data = await reader.read(LIMIT)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception as e:
        print(e)
    finally:
        writer.close()


class Frpc:
    def __init__(self, serve_host, serve_port, local_host, local_port):
        self.serve_host = serve_host
        self.serve_port = serve_port
        self.local_host = local_host
        self.local_port = local_port

    async def heartbeat(self, reader, writer):
        while 1:
            writer.write(b'1')
            await asyncio.sleep(10)

    async def start_tunnel(self):
        serve_reader, serve_writer = await asyncio.open_connection(host=self.serve_host, port=self.serve_port)
        user_reader, user_writer = await asyncio.open_connection(host=self.local_host, port=self.local_port)
        serve_writer.write(b'2')
        asyncio.ensure_future(stream_copy(user_reader, serve_writer))
        asyncio.ensure_future(stream_copy(serve_reader, user_writer))

    async def connect(self):
        reader, writer = await asyncio.open_connection(host=self.serve_host, port=self.serve_port)
        print("connect")
        task = asyncio.ensure_future(self.heartbeat(reader, writer))
        try:
            while not reader.at_eof():
                data = await reader.read(1)
                if not data:
                    raise ConnectionRefusedError('serve close')
                if data == b'1':
                    print("heartbeat")
                elif data == b'2':
                    print("start tunnel")
                    await self.start_tunnel()

        finally:
            task.cancel()
            writer.close()

    async def start(self):
        while 1:
            try:
                await self.connect()
            except Exception as e:
                print(e)
            await asyncio.sleep(5)
            print('reconnect')


async def main(serve_host, serve_port, local_host, local_port):
    await Frpc(serve_host, serve_port, local_host, local_port).start()


if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--serve_host', type=str, default='localhost')
    argparse.add_argument('--serve_port', type=int, default=8800)
    argparse.add_argument('--local_host', type=str, default='localhost')
    argparse.add_argument('--local_port', type=int, default=8080)
    args = argparse.parse_args()
    asyncio.run(main(args.serve_host, args.serve_port, args.local_host, args.local_port))
