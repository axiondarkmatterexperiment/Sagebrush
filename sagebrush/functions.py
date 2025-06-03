import logging
logger = logging.getLogger(__name__)
import math
import numpy as np

#lin-log is log(x)
#log-lin is log(y)

def piecewise_cal(values_x, values_y, this_x, log_x=False, log_y=False):
    if log_x:
        logger.debug("doing log x cal")
        values_x = [math.log(x) for x in values_x]
        if this_x <= 0:
            logger.warning("invalid value for a log function")
            return 1e9
        this_x = math.log(this_x)
    if log_y:
        logger.debug("doing log y cal")
        values_y = [math.log(y) for y in values_y]


    #to_return = np.interp(this_x, values_x, values_y, left = values_y[0], right = values_y[-1])
    index = np.argmin(np.abs(np.array(values_x) - this_x) )
    if index == len(values_x)-1:
        logger.warning("raw value is above the calibration range, extrapolating")
        high_index = index
    elif index == 0:
        high_index = 1
        logger.warning("raw value is below the calibration range, extrapolating")
    else:
        diff1 = np.abs(values_x[index+1] - this_x)
        diff2 = np.abs(values_x[index-1] - this_x)
        if diff1 < diff2: high_index = index+1
        else : high_index = index
        #raise dripline.core.DriplineValueError("raw value is below calibration range")
    m = (values_y[high_index] - values_y[high_index - 1]) / (values_x[high_index] - values_x[high_index - 1])
    to_return = values_y[high_index - 1] + m * (this_x - values_x[high_index - 1])
    if log_y:
        to_return = math.exp(to_return)
    return to_return
