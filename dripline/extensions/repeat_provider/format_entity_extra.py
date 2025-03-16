import asteval # used for FormatEntity
import re # used for FormatEntity

from _dripline.core import op_t
from dripline.implementations import FormatEntity
from dripline.core import calibrate, ThrowReply

import logging
logger = logging.getLogger(__name__)

__all__ = []

__all__.append('FormatEntityExtra')
class FormatEntityExtra(FormatEntity):
    def __init__(self,**kwargs):
        FormatEntity.__init__(self,**kwargs)  

    @calibrate()
    def on_get(self):
        if self._get_str is None:
            # exceptions.DriplineMethodNotSupportedError
            raise ThrowReply('message_error_invalid_method', f"endpoint '{self.name}' does not support get")
        rk = self.name##should be name of endpoint
        request_message = {
          "msgop": op_t.get,
          "specifier": f"{on_get}", 
          "payload":{"values": [self._get_str]}
          }
        result = self.service._send_request(**request_message)
        #"timeout": 10.,

        logger.debug(f'result is: {result}')
        if self._extract_raw_regex is not None:
            first_result = result
            matches = re.search(self._extract_raw_regex, first_result)
            if matches is None:
                logger.error('matching returned none')
                raise ThrowReply('service_error_invalid_value', 'device returned unparsable result, [{}] has no match to input regex [{}]'.format(first_result, self._extract_raw_regex))
            logger.debug(f"matches are: {matches.groupdict()}")
            result = matches.groupdict()['value_raw']
        return result

    def on_set(self, value):
        if self._set_str is None:
            # exceptions.DriplineMethodNotSupportedError
            raise ThrowReply('message_error_invalid_method', f"endpoint '{self.name}' does not support set")
        if isinstance(value, str) and self._set_value_lowercase:
            value = value.lower()
        if self._set_value_map is None:
            mapped_value = value
        elif isinstance(self._set_value_map, dict):
            mapped_value = self._set_value_map[value]
        elif isinstance(self._set_value_map, str):
            mapped_value = self.evaluator(self._set_value_map.format(value))
        logger.debug(f'value is {value}; mapped value is: {mapped_value}')
        request_message = {
          "msgop": op_t.set,
          "specifier": f"{on_set}",
          "payload":{"values": [self._set_str]}
          }
        result = self.service._send_request(**request_message)
        #return self.service.send_to_device([self._set_str.format(mapped_value)])
  
