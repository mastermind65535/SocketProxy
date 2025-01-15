from socket import *
from threading import Thread
from argparse import ArgumentParser
import time
import logging
import traceback
import os

if not os.path.exists("logs"):
    os.mkdir("logs")

ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
</head>
<style>
    p {
        margin: 25px;
    }
    pre {
        margin: 25px;
    }
</style>
<body style="background-color:red;color:white;">
    <h1>Server Error</h1>
    <p>This Page is created by proxy server.</p>
    <p>Your proxy server encountered a <u>critical error</u> while connecting to the remote server.</p>
    <p>Please contact the proxy manager for assistance.</p>
    <p>If the issue are not fixed, Pleaes type the url manually.</p>
    <p>Error Message:</p>
    <pre>{error_message}</pre>
</body>
</html>
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t%(levelname)s - %(message)s"
)

logger = logging.getLogger("SocketProxy")
logger.setLevel(logging.INFO)

FILE_LOGGER = logging.FileHandler(f"logs/{time.strftime('%Y-%m-%d-%H-%M')}.Log")
FILE_LOGGER.setLevel(logging.INFO)
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

CONSOLE_LOGGER = logging.StreamHandler()
CONSOLE_LOGGER.setLevel(logging.INFO)
CONSOLE_LOGGER.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(FILE_LOGGER)
logger.addHandler(CONSOLE_LOGGER)

class SocketProxy:
    def __init__(self, PORT:int, chunk=1048576):
        self.OBJ = socket(AF_INET, SOCK_STREAM)
        self.OBJ.bind(("", int(PORT)))
        self.CHUNK = int(chunk)
        self.EstablishedResponse = b"HTTP/1.1 200 Connection established\r\n\r\n"
        self.STOP = False
    def Handler(self, ClientObj, ADDRESS):
        try:
            REQ = ClientObj.recv(self.CHUNK)
            logger.info(f"REQUEST FROM [{ADDRESS[0]}]:{ADDRESS[1]} ->\t{REQ}")
            RemoteHost, RemotePort = REQ.decode().split()[1].split(":")
            RemoteObj = socket(AF_INET, SOCK_STREAM)
            RemoteObj.connect((str(RemoteHost), int(RemotePort)))
            ClientObj.send(self.EstablishedResponse)
            RemoteThread = Thread(target=self.relay, args=(ClientObj, RemoteObj,))
            ClientThread = Thread(target=self.relay, args=(RemoteObj, ClientObj,))
            RemoteThread.start()
            ClientThread.start()
        except:
            logger.critical(traceback.format_exc().replace("\n", "\n\t"))
            ClientObj.send(self.EstablishedResponse)
            ClientObj.send(ERROR_PAGE.replace("{error_message}", traceback.format_exc()).encode())
    def relay(self, src, dst):
        while not self.STOP:
            try:
                DATA = src.recv(self.CHUNK)
                if not DATA:
                    break
                dst.send(DATA)
            except:
                logger.error(traceback.format_exc().replace("\n", "\n\t"))
                break
    def start(self):
        while not self.STOP:
            self.OBJ.listen()
            SOCKET, ADDRESS = self.OBJ.accept()
            Handler = Thread(target=self.Handler, args=(SOCKET,ADDRESS,))
            Handler.start()

ARGUMENT = ArgumentParser()
ARGUMENT.add_argument("-p", "--port", type=int, default=8080, help="Set Proxy Server Port")
ARGUMENT.add_argument("-c", "--chunk", type=int, default=4096, help="Set Data Chunk")

arg = ARGUMENT.parse_args()

Server = SocketProxy(PORT=arg.port, chunk=arg.chunk)
Server.start()