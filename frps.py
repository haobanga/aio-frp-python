import asyncio
import argparse

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


class Frps:

    def __init__(self, serve_host, serve_port, user_host, user_port):
        self.serve_host = serve_host
        self.serve_port = serve_port
        self.user_host = user_host
        self.user_port = user_port
        self.user_conns = []
        self.frp_conn = None
        self.frp_serve = None
        self.user_serve = None

    async def heartbeat(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while not reader.at_eof():
                reader, writer = self.frp_conn
                data = await reader.read(1)
                if not data:
                    break
                print("heartbeat")
                writer.write(b'1')
        finally:
            self.frp_conn = None
            writer.close()

    async def accept_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self.frp_conn is None:
            writer.close()
        else:
            self.user_conns.append((reader, writer))
            frps_reader, frps_writer = self.frp_conn
            frps_writer.write(b'2')
            await frps_writer.drain()

    async def accept_frp_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        cmd = await reader.read(1)
        if cmd == b'1':
            print("client conn")
            self.frp_conn = (reader, writer)
            asyncio.ensure_future(self.heartbeat(reader, writer))
        elif cmd == b'2':
            print("start tunnel")
            user_reader, user_writer = self.user_conns.pop()
            asyncio.ensure_future(stream_copy(reader, user_writer))
            asyncio.ensure_future(stream_copy(user_reader, writer))

    async def start(self):
        self.frp_serve = await asyncio.start_server(self.accept_frp_connection,
                                                    host=self.serve_host,
                                                    port=self.serve_port)
        self.user_serve = await asyncio.start_server(self.accept_connection,
                                                     host=self.user_host,
                                                     port=self.user_port)
        print("frp serve running on {}:{}".format(self.serve_host, self.serve_port))
        print("user serve running on {}:{}".format(self.user_host, self.user_port))
        try:
            await self.user_serve.start_serving()
            await self.frp_serve.serve_forever()
        finally:
            self.user_serve.close()
            self.frp_serve.close()
            await self.user_serve.wait_closed()
            await self.frp_serve.wait_closed()


async def main(serve_host, serve_port, user_host, user_port):
    await Frps(serve_host, serve_port, user_host, user_port).start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve_host', default='localhost')
    parser.add_argument('--serve_port', default=8800, type=int)
    parser.add_argument('--user_host', default='localhost')
    parser.add_argument('--user_port', default=8801, type=int)
    args = parser.parse_args()
    asyncio.run(main(args.serve_host, args.serve_port, args.user_host, args.user_port))
