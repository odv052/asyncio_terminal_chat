import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(
    format='{levelname} {funcName}: {message}',
    style='{',
    level=logging.INFO,
)


async def display_chat(reader):
    logging.info('start listen server')
    while True:
        if reader.at_eof():
            logging.info('lost server connection')
            print('Connection was closed by server')
            break
        update = await reader.read(100)
        print(f'{datetime.now():%H:%M:%S} {update.decode()}')


async def send_message(writer):
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()  # loop=loop)
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

    logging.info('start listen user input')
    while True:
        line = await reader.readline()
        if not line:
            break
        line = line.strip()
        writer.write(line)
        await writer.drain()


async def client(client_name):
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    except ConnectionRefusedError:
        print('Cannot connect to server')
        return
    # send client name to server
    writer.write(f'client_name:{client_name}'.encode())
    await writer.drain()

    try:
        await asyncio.wait(
            (display_chat(reader), send_message(writer)),
            return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        writer.close()

name = input('Your name in chat: ')
try:
    asyncio.run(client(name))
except KeyboardInterrupt:
    pass
