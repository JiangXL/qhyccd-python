# qhyccd-python
The QHYCCD SDK wrapper in Python. This project still is under construction
for laboratory usage, but you can find the most fundamental thing in the
Jupyter Notebook. Then you can make you own python wrapper and have a good
day.

These scripts only test on Linux, but should run in windows and OS X
with little modification.

QHYCCD SDK should be installed on you system. `libqhyccd.so` should be found
on `/usr/local/lib/libqhyccd/so`, or you need to update pathway in 
`qhyccd.py`.

## Usage
```python
import qhyccd # import qhyccd wrapper
import numpy as np

qc = qhyccd.qhyccd() # create qhyccd object
qc.SetExposure(qc, 1000) # set exposure to 1000ms
image = qc.GetSingleFrame() # return image
```
