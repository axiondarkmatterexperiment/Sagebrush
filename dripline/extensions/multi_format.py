'''
Dan Zhang  migrate DL2 to DL3 multi format entity to send multiple commands at once
'''

import re # used for FormatEntity
import asteval
import yaml
import json
from dripline.core import Entity, calibrate, ThrowReply

import logging
logger = logging.getLogger(__name__)

__all__ = ['MultiFormatEntity']


_all_calibrations = []


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
