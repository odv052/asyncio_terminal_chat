import asyncio
import functools
import logging

logging.basicConfig(
    format='{levelname} {funcName}: {message}',
    style='{',
    level=logging.INFO
)


async def rw_handler(reader, writer, writers_pool):
    peername = writer.get_extra_info("peername")[1]
    logging.info(f'connected {peername}')

    # get client name
    client_name = (await reader.read(100)).decode()

    # disconnect client if name not provided
    if not all((client_name.startswith('client_name:'), len(client_name) > 5)):
        writer.write(b'First message should be in format "client_name:{client_name}"')
        await writer.drain()
        writer.close()
        logging.info(f'disconnected {peername}: name was not provided')
        return

    writers_pool.add(writer)
    client_name = client_name.rsplit(':')[1]
    client_name_encoded = client_name.encode()
    client_id = ':'.join((str(peername), client_name))
    logging.info(f'connection accepted {client_id}. Start listening')

    while True:
        b_message = (await reader.read(100))

        if reader.at_eof():
            logging.info(f'disconnected {client_id}')
            writers_pool.remove(writer)
            break

        b_message = b': '.join((client_name_encoded, b_message))
        sent_count = 0
        for recipient_writer in writers_pool:
            # do not sent message to origin
            if recipient_writer is writer:
                continue

            recipient_writer.write(b_message)
            await recipient_writer.drain()
            sent_count += 1
            logging.info(f'write message from {client_name} to {sent_count} recipients')


async def main():
    writers = set()
    server = await asyncio.start_server(
        client_connected_cb=functools.partial(rw_handler, writers_pool=writers),
        host='127.0.0.1',
        port=8888,
    )

    addr = server.sockets[0].getsockname()
    logging.info(f'serving on {addr}')

    try:
        async with server:
            logging.info('start server')
            await server.serve_forever()
    finally:
        for writer in writers:
            writer.close()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
