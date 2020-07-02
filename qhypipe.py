import qhyccd
import time
import numpy as np
import SocketTransfer

qc = qhyccd.qhyccd()

server = SocketTransfer.socket_sender()

server.accept()


def live():
    qc.BeginLive()
    while(True):
        #time.sleep(0.001)
        img = qc.GetLiveFrame()
        server.send_img( img )
    qc.StopLive()
    
