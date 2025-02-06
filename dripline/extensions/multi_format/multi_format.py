'''
Dan Zhang  migrate DL2 to DL3 multi format entity to send multiple commands at once
'''

import re # used for FormatEntity
import asteval
import yaml
import json
from dripline.core import Entity, calibrate, ThrowReply
import numpy as np
import rf_fitting as fitting

import logging
logger = logging.getLogger(__name__)

__all__ = ['MultiFormatEntity']


_all_calibrations = []

def debug_calibration(data_object):
    logger.info("data string zero is {}".format(data_object["start_frequency"]))
    return data_object
_all_calibrations.append(debug_calibration)

def transmission_calibration(data_object):
    """takes a network analyzer output of format 
            {
        start_frequency: <number>
        stop_frequency: <number>
        iq_data: <array of numbers, packed i,r,i,r>
            }
        and augments it with a transmission fit
          {
        fit_f0: <number>
        fit_Q: <number>
        fit_norm: <number>
        fit_noise: <number>
        fit_chisq: <number>
          }
    """
    freqs=np.linspace(data_object["start_frequency"],data_object["stop_frequency"],int(len(data_object["iq_data"])/2))
    powers=fitting.iq_packed2powers(data_object["iq_data"])
    fit_norm,fit_f0,fit_Q,fit_noise,fit_chisq,fit_shape=fitting.fit_transmission(powers,freqs)
    data_object["fit_norm"]=fit_norm
    data_object["fit_f0"]=fit_f0
    data_object["fit_Q"]=fit_Q
    data_object["fit_noise"]=fit_noise
    data_object["fit_chisq"]=fit_chisq
    data_object["fit_shape"]=fit_shape
    return data_object
#return data
_all_calibrations.append(transmission_calibration)

def sidecar_transmission_calibration(data_object):
    """takes a network analyzer output of format 
            {
        start_frequency: <number>
        stop_frequency: <number>
        iq_data: <array of numbers, packed i,r,i,r>
            }
        and augments it with a transmission fit
          {
        fit_f0: <number>
        fit_Q: <number>
        fit_norm: <number>
        fit_noise: <number>
        fit_chisq: <number>
          }
    """
    freqs=np.linspace(data_object["start_frequency"],data_object["stop_frequency"],int(len(data_object["iq_data"])/2))
    powers=fitting.iq_packed2powers(data_object["iq_data"])
    fit_output = fitting.sidecar_fit_transmission(powers,freqs)
    data_object["fit_norm"]=fit_output[0]
    data_object["fit_f0"]=fit_output[1]
    data_object["fit_Q"]=fit_output[2]
    data_object["fit_noise"]=fit_output[3]
    data_object["fit_chisq"]=fit_output[4]
    data_object["fit_shape"]=fit_output[5]
    return data_object
#return data
_all_calibrations.append(sidecar_transmission_calibration)
    
def reflection_calibration(data_object):
    """takes a network analyzer output of format 
            {
        start_frequency: <number>
        stop_frequency: <number>
        iq_data: <array of numbers, packed i,r,i,r>
            }
        and augments it with a transmission fit
          {
        fit_f0: <number>
        fit_Q: <number>
        fit_norm: <number>
        fit_noise: <number>
        fit_chisq: <number>
          }
    """
    freqs=np.linspace(data_object["start_frequency"],data_object["stop_frequency"],int(len(data_object["iq_data"])/2))
    fit_norm,fit_phase,fit_f0,fit_Q,fit_beta,fit_delay_time,fit_chisq,dip_depth,fit_shape=fitting.fit_reflection(data_object["iq_data"],freqs)
    data_object["fit_norm"]=fit_norm
    data_object["fit_phase"]=fit_phase
    data_object["fit_f0"]=fit_f0
    data_object["fit_Q"]=fit_Q
    data_object["fit_beta"]=fit_beta
    data_object["fit_delay_time"]=fit_delay_time
    data_object["fit_chisq"]=fit_chisq
    data_object["fit_shape"]=fit_shape
    data_object["dip_depth"]=dip_depth
    return data_object
_all_calibrations.append(reflection_calibration)


def sidecar_reflection_calibration(data_object):
    """takes a network analyzer output of format 
            {
        start_frequency: <number>
        stop_frequency: <number>
        iq_data: <array of numbers, packed i,r,i,r>
            }
        and augments it with a reflection fit
          {
        fit_f0: <number>
        fit_Q: <number>
        fit_norm: <number>
        fit_noise: <number>
        fit_chisq: <number>
          }
    """
    freqs = np.linspace(data_object["start_frequency"],
                        data_object["stop_frequency"],
                        int(len(data_object["iq_data"])/2))

    fit_output = fitting.sidecar_fit_reflection(data_object["iq_data"], freqs)
    data_object["fit_norm"] = fit_output[0]
    data_object["fit_phase"] = fit_output[1]
    data_object["fit_f0"] = fit_output[2]
    data_object["fit_Q"] = fit_output[3]
    data_object["fit_beta"] = fit_output[4]
    data_object["fit_delay_time"] = fit_output[5]
    data_object["fit_chisq"] = fit_output[6]
    data_object["fit_shape"] = fit_output[7]
    data_object["dip_depth"] = fit_output[8]
    return data_object
_all_calibrations.append(sidecar_reflection_calibration)

def widescan_calibration(data_object):
    """takes a network analyzer output of format 
            {
        start_frequency: <number>
        stop_frequency: <number>
        iq_data: <array of numbers, packed i,r,i,r>
            }
        and augments it with crude peak finding
          {
        peak_freqs: <array of frequencies>
          }
    """
    powers=fitting.iq_packed2powers(data_object["iq_data"])
    data_fraction=0.05 #5 percent seems to work, change as you please
    data_object["peaks"]=fitting.find_peaks(powers,data_fraction,data_object["start_frequency"],data_object["stop_frequency"]).tolist()
    return data_object
_all_calibrations.append(widescan_calibration)

def semicolon_array_to_json_object(data_string,label_array):
    #Convert a bunch of values separated by semicolons into a json object
    #make a best guess as to whether the values are supposed to be arrays, numbers, or strings
    split_strings=data_string.split(";")
    data_object={}
    if len(split_strings)<len(label_array):
        raise ThrowReply("not enough values given to fill semicolon_array")
    for i in range(len(label_array)):
        if "," in split_strings[i]:
            #we assume that if there are commas, it must mean an array
            elems=split_strings[i].split(',')
            my_array=[]
            for x in elems:
                try:
                    my_array.append(float(x))
                except ValueError: #otherwise it must be a string
                    my_array.append(x)
            data_object[ label_array[i] ]=my_array
        else:
            try: #if it acts like a float, assume its a number
                data_object[ label_array[i] ]=float(split_strings[i])
            except ValueError: #otherwise it must be a string
                data_object[ label_array[i] ]=split_strings[i]
    return json.dumps(data_object)
    


_all_calibrations.append(semicolon_array_to_json_object)


class MultiFormatEntity(Entity):
    '''In standard SCPI, you should be able to send a bunch of requests separated by colons
       This spime does this and returns a json structure organized by label'''
    def __init__(self,
                 get_commands=None,
                 set_commands=None,
                 **kwargs):
        '''
        get_commands would be expected to be a list of get type commands
        set_commands would be expected to be a list of set type commands
        '''
        Entity.__init__(self, **kwargs)
        self._get_commands=get_commands
        self._set_commands=set_commands
   
    


    @calibrate(_all_calibrations)

    def on_get(self):
        if self._get_commands is None:
            raise ThrowReply('<{}> has no get commands available'.format(self.name))
        get_labels=[]
        to_send=""
        for i in range(len(self._get_commands)):
            if i!=0:
                to_send=to_send+";"
            to_send=to_send+self._get_commands[i]["get_str"]
            get_labels.append(self._get_commands[i]["label"])
        result = self.service.send_to_device([to_send])
        return semicolon_array_to_json_object(result,get_labels)

    def on_set(self,value): ##value is expected to be in a yaml format
        if self._set_commands is None:
            raise ThrowReply('<{}> has no set commands available'.format(self.name))
        try:
            value_structure=yaml.safe_load(value) 
        except yaml.YAMLError as exc:
            raise ThrowReply('<{}> had error {}'.format(self.name,exc)) 
        to_send=""
        for command in self._set_commands:
            if command["label"] in value_structure:
                if len(to_send)>0:
                    to_send=to_send+";"
                to_send+="{} {}".format(command["set_str"],value_structure[command["label"]])
        to_send=to_send+";*OPC?"
        result = self.service.send_to_device([to_send])
        return result
