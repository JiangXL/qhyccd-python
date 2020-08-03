#!/bin/python3
import ctypes
from ctypes import *
import numpy as np
import time
from libqhy import *

"""
Basic functions to control qhyccd camera

| Version | Commit
| 0.1     | initial version @2020/07/02 hf

#TODO: fail to change steammode inside sdk
"""

class qhyccd():
    def __init__(self):
        # create sdk handle
        self.sdk= CDLL('/usr/local/lib/libqhyccd.so')
        self.sdk.GetQHYCCDParam.restype = c_double
        self.sdk.OpenQHYCCD.restype = ctypes.POINTER(c_uint32)
        # ref: https://www.qhyccd.com/bbs/index.php?topic=6356.0
        self.mode = 0 # Default stream mode is single frame, 0 for single frame
        self.bpp = c_uint(8) # 8 bit
        self.exposureMS = 100 # 100ms
        self.connect(self.mode)

    def connect(self, mode):
        ret = -1
        self.sdk.InitQHYCCDResource()
        self.sdk.ScanQHYCCD()
        type_char_array_32 = c_char*32
        self.id = type_char_array_32()
        self.sdk.GetQHYCCDId(c_int(0), self.id)    # open the first camera
        print("Open camera:", self.id.value)
        self.cam = self.sdk.OpenQHYCCD(self.id)
        self.sdk.SetQHYCCDStreamMode(self.cam, self.mode)  
        self.sdk.InitQHYCCD(self.cam)

        # Get Camera Parameters
        self.chipw = c_double()
        self.chiph = c_double()
        self.w = c_uint()
        self.h = c_uint()
        self.pixelw = c_double()
        self.pixelh = c_double() 
        self.channels = c_uint32(1)
        self.sdk.GetQHYCCDChipInfo(self.cam, byref(self.chipw), byref(self.chiph),
                byref(self.w), byref(self.h), byref(self.pixelw),
                byref(self.pixelh), byref(self.bpp))
        self.roi_w = self.w
        self.roi_h = self.h #TODO: keep roi between stream mode change
        self.imgdata = (ctypes.c_uint8 * self.w.value* self.h.value)()
        self.SetExposure( self.exposureMS )
        self.SetBit(self.bpp.value)
        self.SetROI(0, 0, self.w.value, self.h.value)
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_USBTRAFFIC, c_double(10))
        #self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_TRANSFERBIT, self.bpp)
        # Maximum fan speed
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_MANULPWM, c_double(255))
        # Cooler to -15
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_COOLER, c_double(-15))

    def SetStreamMode(self, mode):
        """ TODO: Unable to change"""
        self.sdk.CloseQHYCCD(self.cam)
        self.mode = mode
        self.connect(mode)

    """Set camera exposure in ms, return actual exposure after setting """
    def SetExposure(self, exposureMS):
        # sdk exposure uses us as unit
        self.exposureMS = exposureMS # input ms
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_EXPOSURE, c_double(exposureMS*1000))
        print("Set exposure to", 
                self.sdk.GetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_EXPOSURE)/1000)

    """ Set camera gain """
    def SetGain(self, gain):
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_GAIN, c_double(gain))
    
    """ Set camera depth """
    def SetBit(self, bpp):
        self.bpp.value = bpp
        self.sdk.SetQHYCCDParam(self.cam, CONTROL_ID.CONTROL_TRANSFERBIT, c_double(bpp))

    """ Set camera ROI """
    def SetROI(self, x0, y0, roi_w, roi_h):
        self.roi_w =  c_uint(roi_w)
        self.roi_h =  c_uint(roi_h)
        # update buffer to recive camera image
        if self.bpp.value == 16:
            self.imgdata = (ctypes.c_uint16 * roi_w * roi_h)()
            self.sdk.SetQHYCCDResolution(self.cam, x0, y0, self.roi_w, self.roi_h)
        else: # 8 bit
            self.imgdata = (ctypes.c_uint8 * roi_w * roi_h)()
            self.sdk.SetQHYCCDResolution(self.cam, x0, y0, self.roi_w, self.roi_h)

    """ Exposure and return single frame """
    def GetSingleFrame(self):
        ret = self.sdk.ExpQHYCCDSingleFrame(self.cam)
        ret = self.sdk.GetQHYCCDSingleFrame(
            self.cam, byref(self.roi_w), byref(self.roi_h), byref(self.bpp),
            byref(self.channels), self.imgdata)
        return np.asarray(self.imgdata) #.reshape([self.roi_h.value, self.roi_w.value])
   

    def BeginLive(self):
        """ Begin live mode"""
        self.sdk.SetQHYCCDStreamMode(self.cam, 1)  # Live mode
        self.sdk.BeginQHYCCDLive(self.cam)
    
    def GetLiveFrame(self):
        """ Return live image """
        self.sdk.GetQHYCCDLiveFrame(self.cam, byref(self.roi_h), byref(self.roi_w), 
                byref(self.bpp), byref(self.channels), self.imgdata)
        return np.asarray(self.imgdata)

    def StopLive(self):
        """ Stop live mode, change to single frame """
        self.sdk.StopQHYCCDLive(self.cam)
        self.sdk.SetQHYCCDStreamMode(self.cam, 0)  # Single Mode

    """ Relase camera and close sdk """
    def close(self):
        self.sdk.CloseQHYCCD(self.cam)
        self.sdk.ReleaseQHYCCDResource()
