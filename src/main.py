import sys
import signal
import asyncio
import logging
import argparse

import logger
from service import Service

async def main(args):
    url = f"tcp://{args.server_address}:{args.server_port}"
    service = Service(url, simulate=bool(args.simulate))
    await service.start()

def handler(signum, frame):
    response = input(" CTRL-C was pressed. Do you really want to exit? y/n ")
    if response == "y":
        logging.error("CTRL-C was pressed")
        sys.exit(-1)
signal.signal(signal.SIGINT, handler)

parser = argparse.ArgumentParser(
    prog="pylogix-as-service",
    description="Wraps pylogix with zeromq to allow multi-language inter process communication."
)
parser.add_argument(
    '--server-address',
    dest="server_address",
    required=True,
    help="The address for this service to bind to, eg. 127.0.0.1."
)
parser.add_argument(
    '--server-port',
    dest="server_port",
    required=True,
    help="The port for this service to list on, eg. 7777."
)
parser.add_argument(
    '--simulate',
    dest="simulate",
    default=False,
    required=False,
    help="Simulate connection to the PLC, useful for testing."
)
args = parser.parse_args()

asyncio.run(main(args=args))
