#!/bin/python3
"""Modules for transfer image in local or remote using socket(TCP)

Version | Commit
 0.1    | First version, by H.F, Oct/08/2019
 0.2    | Using non-blocking socket
 0.2.1  | Set timeout in 0.1ms to avoid Windows' no responding Nov/22/2019
 0.3    | Much more reliable: detect exceptions caused by connection failure,
        | then listen, accept, reconnect again. (H.F, Feb/02/2020, 到岭)
 0.3.1  | Support transfer 8bit gray image
Todo: 1. Add context manager type
      2. Add function to recv and sned serilize data instead of matrix
"""

import time
import socket
import struct
import numpy as np

#Ref:https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
#    https://docs.python.org/zh-cn/3/library/struct.html

class general_socket():
    """General class for sender(server) and receiver(client) modules"""
    def __init__(self):
        self.PORT = 60000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__generate_testimg()


    def __generate_testimg(self):
        """Generate 2d-gaussian matrix"""
        # Ref: https://gist.github.com/andrewgiessel/4635563
        size = 1024
        fwm = 300
        x0 = y0 = size//2
        x = np.arange(0, size, 1, float)
        y = x[:,np.newaxis]
        self.testimg = (2**16 * np.exp(-4*np.log(2) * ((x-x0)**2 +
            (y-y0)**2) / fwm**2)).astype(np.uint16)

    def close(self):
        """Close runing socket"""
        self.sock.close() # TODO: may not work in sender

class socket_sender(general_socket):
    """Server Class to Send Image(Blocking Socket Server)"""
    def __init__(self):
        super().__init__()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # avoid "Address already in used"
        self.sock.bind(('0.0.0.0', self.PORT))
        self.sock.listen(7) # only access one connection now
        self.sock.setblocking(0)     # Although self.conn is blocking, self.sock
        self.sock.settimeout(0.0001) # is time-out socket. Time-out socket is
        # 0.0001 second              # useful to print info during  connecting.

    def accept(self):
        """More reliable accept function to accept latest connect request."""
        flag = 0
        while flag < 20000: # Until hass
            try:
                self.conn, addr = self.sock.accept()
                while True: # only choose final request
                    try:    # TODO: need much test for effiency
                        self.conn, addr = self.sock.accept()
                    except socket.timeout:
                        break
                self.conn.setblocking(True) # change to blocking socket
                self.send_img(self.testimg) # send image trigger receiver update
                print("Client", addr, "connected")
                return True
                break
            except socket.timeout:
                flag += 1
                if flag == 1: # only print once
                    print("Waiting receive program")
                elif flag == 20000:
                    print("No receive program found!")
                    print("Please reconnect after opening reveive program")
                    return False
                    break

    def send_img(self, img):
        """Package 8/16 bit gray image and send packaged data."""

        img_bit = int(img.dtype.name[4:]) # image depth 8/16
        img_bytes = img.tobytes()       # Only accept 16 bit gray iamge
        msg = ( struct.pack('>I', len(img_bytes))  # unsigned int, length 4
                + struct.pack('>H',img.shape[0])
               + struct.pack('>H', img.shape[1]) 
               + struct.pack('>H', img_bit) + img_bytes)
        try:
            self.conn.sendall(msg)
        except socket.timeout:
            print("Lost tcp connection")
        except BrokenPipeError:
            print("Fail to send")
            print("BrokenPipeError: Connecttion has lost, need reconnect!")

class socket_receiver(general_socket):
    """Class to Receive Images(Timeout Socket Client)"""
    def __init__(self, HOST):
        super().__init__()
        self.HOST = HOST
        self.isconnected = False
        self.connectStatus = "Waiting"
        self.connect()
        self.sock.setblocking(0)
        self.sock.settimeout(0.0001) # 0.0001 second

    def connect(self):
        """Connect with sender service(blocking)."""
        time.sleep(0.001)     # Add sleep to avoid slug cpu
        if not self.isconnected: # Only update when refresh GUI, due to Windows
            try:                 # will no responing using blocking loop
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.HOST, self.PORT)) # Has to new socket
                self.sock.setblocking(0)                  # TODO: better logic
                self.sock.settimeout(0.0001) # 0.0001s
                self.isconnected = True
                print("Connecting to ", self.sock.getpeername())
                self.connectStatus = "Connecting"
                return "Connecting"
            except ConnectionRefusedError:
                #print("No sender found, need open sender server")
                return "Refuse connect"
        else:
            print("Already connected")
            self.connectStatus = "Connected"
            return "Connected"

    def recvall(self, sock, n):
        """Receive and return speical length stream data byte by byte."""
        data = b''
        while len(data) < n:
            packet = sock.recv( n-len(data))
            if packet == b'':
                raise ConnectionError("Service down")
            data += packet
        return data

    def recv_img(self):
        """Receive and depackage stream data, return image.
        If no image is received, return None.
        """
        # Get frame header and deal with connection error
        try:
            raw_msglen = self.recvall(self.sock, 4) # read image length
        except socket.timeout: # socket timeout error
            return None
        except (ConnectionError, OSError):
            #print("Sender service has down!")
            #print("Need to start sender service again!")
            #print("Waiting new connection")
            self.connectStatus = "Sender Service Down"
            self.isconnected = False
            self.connect()
            return None
        # Then receive and depackage image info frame
        msglen = struct.unpack('>I', raw_msglen)[0]
        raw_height = self.recvall(self.sock, 2)  # read image height
        height = struct.unpack('>H', raw_height)[0]
        raw_width = self.recvall(self.sock, 2)   # read image width
        width = struct.unpack('>H', raw_width)[0]
        raw_bit= self.recvall(self.sock, 2)   # read image depth
        bit = struct.unpack('>H', raw_bit)[0]

        # Finaly, receive and depackage image data frame
        try: # add HF Nov/22/19
            self.connectStatus = "Connected"
            if bit == 16 : # Adapt to different image depth
                return (np.frombuffer(self.recvall(self.sock, msglen),
                    dtype=np.uint16).reshape([height, width]))
            else :
                return (np.frombuffer(self.recvall(self.sock, msglen),
                    dtype=np.uint8).reshape([height, width]))

        except AttributeError:
            return None
