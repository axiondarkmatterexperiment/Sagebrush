import re # used for FormatEntity
import asteval
import yaml
import json
from dripline.core import calibrate, ThrowReply
from dripline.implementations import FormatEntity
import time
import logging
logger = logging.getLogger(__name__)

__all__ = ['UnstableFormatEntity']

class UnstableFormatEntity(FormatEntity):
    def __init__(self, n_trials, **kwargs):
        self._n_trials = int(n_trials)
        FormatEntity.__init__(self,**kwargs)


    @calibrate()
    def on_get(self):
        Ntrials = self._n_trials
        index = 0
        if self._get_str is None:
            # exceptions.DriplineMethodNotSupportedError
            raise ThrowReply('message_error_invalid_method', f"endpoint '{self.name}' does not support get")
        result = self.service.send_to_device([self._get_str])
        logger.debug(f'result is: {result}')
        if self._extract_raw_regex is not None:
            matches = re.search(self._extract_raw_regex, result)
            while matches is None and Ntrials > 0:
                logger.debug(f'result is: {result} {index}')
                logger.error('matching returned none')
                self.service._reconnect()
                time.sleep(1)
                logger.debug(f'try reconnect')
                result = self.service.send_to_device([self._get_str])
                matches = re.search(self._extract_raw_regex, result)
                time.sleep(1)
                index +=1
                Ntrials -=1
            
            if matches is None:    
                raise ThrowReply('service_error_invalid_value', 'device returned unparsable result, [{}] has no match to input regex [{}]'.format(first_result, self._extract_raw_regex))
            logger.debug(f"matches are: {matches.groupdict()}")
            result = matches.groupdict()['value_raw']
        return result
