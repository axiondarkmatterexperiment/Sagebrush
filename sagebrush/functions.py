import logging
logger = logging.getLogger(__name__)
import math


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
    try:
        high_index = [i>this_x for i in values_x].index(True)
    except ValueError:
        high_index = -1
        logger.warning("raw value is above the calibration range, extrapolating")
        #raise dripline.core.DriplineValueError("raw value is likely above calibration range")
    if high_index == 0:
        high_index = 1
        logger.warning("raw value is below the calibration range, extrapolating")
        #raise dripline.core.DriplineValueError("raw value is below calibration range")
    m = (values_y[high_index] - values_y[high_index - 1]) / (values_x[high_index] - values_x[high_index - 1])
    to_return = values_y[high_index - 1] + m * (this_x - values_x[high_index - 1])
    if log_y:
        to_return = math.exp(to_return)
    return to_return
