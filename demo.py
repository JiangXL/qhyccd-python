import qhyccd # import qhyccd wrapper
import numpy as np

qc = qhyccd.qhyccd() # create qhyccd object
qc.SetExposure(qc, 1000) # set exposure to 1000ms
image = qc.GetSingleFrame()

