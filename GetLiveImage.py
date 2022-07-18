import qhyccd
import time
import numpy as np
from time import strftime,localtime

qc = qhyccd.qhyccd()

def live():
    qc.BeginLive()
    while(True):
        #time.sleep(0.001)
        img = qc.GetLiveFrame()
        server.send_img( img )
        #print( time.monotonic() )
    qc.StopLive()

def seq_capture_0924(intervalS, durationMin, name):
    print("Begin Sequence Capture, interval:", intervalS, "s duration:", durationMin, "min")
    qc.SetExposure(100)
    qc.SetGain(1)
    qc.SetROI(400, 0, 3522, 3522)
    counter = 0
    total_cycle = int(durationMin * 60 // intervalS)
    t_start = time.monotonic()
    
    state = 0
    qc.BeginLive()
    print("Star capture at", strftime("%Y-%m-%d %H:%M:%S", localtime()) ) 
    for t in range(total_cycle + 4):
        t_start = time.monotonic()
        img = qc.GetLiveFrame()
        print("*", end="")
        while(time.monotonic() - t_start < intervalS):
            time.sleep(0.001)
    print()
    print("Stop capture at", strftime("%Y-%m-%d %H:%M:%S", localtime()) ) 

