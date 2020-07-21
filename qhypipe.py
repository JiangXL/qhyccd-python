import qhyccd
import time
import numpy as np
import SocketTransfer
import cv2 as cv

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

def seq_capture(interval, duration, folder):
    print("Begin Sequence Capture, interval:", interval, "duration:", duration )
    counter = 0
    total_cycle = duration * 60 // (interval)
    t_start = time.monotonic()

    state = 0
    qc.BeginLive()
    for t in range(total_cycle):
        t_start = time.monotonic()
        img = qc.GetLiveFrame()
        cv.imwrite(folder+"%06d.tif"%t, img) 
        while(time.monotonic() - t_start < interval):
            time.sleep(0.1)

        


