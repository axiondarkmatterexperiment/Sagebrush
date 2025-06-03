'''
A class to interface with the multiplexer aka muxer instrument
'''

from dripline.core import ThrowReply, Entity, calibrate
from dripline.implementations import EthernetSCPIService
from dripline.implementations.entity_endpoints import FormatEntity
from sagebrush.functions import piecewise_cal
from dripline.extensions.calibration_data import process_chan1_U09595, process_chan2_x76420, process_chan3_x76422,process_chan4_U08256,process_chan5_Hexframe_Temp_Sensor, process_chan6_U06390, process_chan7_U08257, process_chan8_U08259, process_chan9_U06344, process_chan10_Coldfinger_Temp_Sensor, process_chan11_RuOx102a2, process_chan12_U09597
import numpy as np
import logging
logger = logging.getLogger(__name__)

__all__ = []

_all_calibrations = []


def U09595(resistance):
    values_x = process_chan1_U09595.x
    values_y = process_chan1_U09595.y
    result = piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
    return result
_all_calibrations.append(U09595)


def x76420(resistance):
    values_x = process_chan2_x76420.x
    values_y = process_chan2_x76420.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(x76420)

def x76422(resistance):
    values_x = process_chan3_x76422.x
    values_y = process_chan3_x76422.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(x76422)

def U08256(resistance):
    values_x = process_chan4_U08256.x
    values_y = process_chan4_U08256.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U08256)

def Hexframe_Temp_Sensor(resistance):
    values_x = process_chan5_Hexframe_Temp_Sensor.x
    values_y = process_chan5_Hexframe_Temp_Sensor.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(Hexframe_Temp_Sensor)

def U06390(resistance):
    values_x = process_chan6_U06390.x
    values_y = process_chan6_U06390.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U06390)

def U08257(resistance):
    values_x = process_chan7_U08257.x
    values_y = process_chan7_U08257.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U08257)

def U08259(resistance):
    values_x = process_chan8_U08259.x
    values_y = process_chan8_U08259.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U08259)

def U06344(resistance):
    values_x = process_chan9_U06344.x
    values_y = process_chan9_U06344.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U06344)


def Coldfinger_Temp_Sensor(resistance):
    values_x = process_chan10_Coldfinger_Temp_Sensor.x
    values_y = process_chan10_Coldfinger_Temp_Sensor.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(Coldfinger_Temp_Sensor)

def RuOx102a2(resistance):
    values_x = process_chan11_RuOx102a2.x
    values_y = process_chan11_RuOx102a2.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(RuOx102a2)


def U09597(resistance):
    values_x = process_chan12_U09597.x
    values_y = process_chan12_U09597.y
    return piecewise_cal(values_x, values_y, float(resistance), log_x=True, log_y=True)
_all_calibrations.append(U09597)


__all__.append('LSEntity')
class LSEntity(FormatEntity):
    '''
    Entity for communication with muxer endpoints.  No set functionality.
    '''

    def __init__(self,
                 ch_number,
                 **kwargs):
        '''
        ch_number (int): channel number for endpoint
        conf_str (str): used by MuxerService to configure endpoint scan
        '''
        Entity.__init__(self, **kwargs)
        self.get_str = f"RDGR? {ch_number}"

    @calibrate(_all_calibrations)

    def on_get(self):
        result = self.service.send_to_device([self.get_str])
        logger.debug('very raw is: {}'.format(result))
        return result.split()[0]

    def on_set(self, value):
        raise ThrowReply('message_error_invalid_method',
                        f'endpoint {self.name} does not support set')
