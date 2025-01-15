from socket import *
from threading import Thread
from argparse import ArgumentParser
import time
import logging
import traceback
import os

if not os.path.exists("logs"):
    os.mkdir("logs")

logger = logging.getLogger("SocketProxy")
logger.setLevel(logging.INFO)

FILE_LOGGER = logging.FileHandler(f"logs/{time.strftime('%Y-%m-%d-%H-%M')}.Log")
FILE_LOGGER.setLevel(logging.INFO)
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

CONSOLE_LOGGER = logging.StreamHandler()
CONSOLE_LOGGER.setLevel(logging.INFO)
CONSOLE_LOGGER.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

logger.addHandler(FILE_LOGGER)
logger.addHandler(CONSOLE_LOGGER)

class SocketProxy:
    def __init__(self, port=8080, chunk=1024):
        self.PORT = int(port)
        self.CHUNK = int(chunk)
        self.ProxyServer = socket(AF_INET, SOCK_STREAM)
        self.ProxyServer.bind(("", self.PORT))
        self.EstablishedResponse = b"HTTP/1.1 200 Connection established\r\n\r\n"
        self.ProtocolSupport = ["http", "https"]
    def parseServer(self, REQ:bytes):
        URL = REQ.decode().split()[1].split(":")
        if URL[0] in self.ProtocolSupport:
            RemoteHost = str(URL[1]).split("//")[1]
            RemotePort = int(getservbyname(URL[0]))
            return RemoteHost, RemotePort
        RemoteHost = str(REQ.decode().split()[1].split(":")[0])
        RemotePort = int(REQ.decode().split()[1].split(":")[1])
        return RemoteHost, RemotePort
    def connector(self, Host:str, Port:int):
        try:
            RemoteObj = socket(AF_INET, SOCK_STREAM)
            RemoteObj.connect((str(Host), int(Port)))
            return RemoteObj
        except Exception as e:
            logger.error(f"Error\t: {e}")
            return False
    def relay(self, src:object, dst:object):
        while True:
            try:
                DATA = src.recv(self.CHUNK)
                if not DATA:
                    break
                dst.send(DATA)
            except Exception as e:
                logger.error(f"Error\t: {e}")
                break
    def Handler(self, Client:object):
        try:
            REQUEST = Client.recv(self.CHUNK)
            RemoteHost, RemotePort = self.parseServer(REQ=REQUEST)
            Remote = self.connector(Host=RemoteHost, Port=RemotePort)
            if Remote == False:
                logger.error(f"Error\t: {REQUEST}")
                Client.close()
                return
            logger.info(f"Bridge\t: [{RemoteHost}]:{RemotePort}")
            Client.send(self.EstablishedResponse)
            RemoteBridge = Thread(target=self.relay, args=(Client, Remote))
            ClientBridge = Thread(target=self.relay, args=(Remote, Client))
            RemoteBridge.start()
            ClientBridge.start()
        except Exception as e:
            logger.critical(f"Error\t: {e}")
    def start(self):
        while True:
            self.ProxyServer.listen()
            SOCKET, ADDRESS = self.ProxyServer.accept()
            logger.info(f"Client\t: [{ADDRESS[0]}]:{ADDRESS[1]}")
            Handler = Thread(target=self.Handler, args=(SOCKET,))
            Handler.start()

ARGUMENT = ArgumentParser()
ARGUMENT.add_argument("-p", "--port", type=int, default=8080, help="Set Proxy Server Port")
ARGUMENT.add_argument("-c", "--chunk", type=int, default=4096, help="Set Data Chunk")

arg = ARGUMENT.parse_args()

Server = SocketProxy(port=arg.port, chunk=arg.chunk)
Server.start()