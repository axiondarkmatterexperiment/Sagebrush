import re
import socket
import threading

from dripline.core import Service, ThrowReply, Entity, calibrate

import logging
logger = logging.getLogger(__name__)

__all__ = []

__all__.append('JACOBEntity')
class JACOBEntity(Entity):
    def __init__(self,
                 cmd_str=None,
                 **kwargs):
        '''
        Args:
            cmd_str (str): query string to send to jacob
        '''
        Entity.__init__(self, **kwargs)
        if cmd_str is None:
            raise ThrowReply('service_error_invalid_value', '<base_str> is required to __init__ SimpleSCPIEntity instance')
        else:
            self.cmd_str = cmd_str

    """ Will return just the whole response as a vector of strings"""
    @calibrate()
    def on_get(self):
        result=self.service.send_to_device(self.cmd_str)
        result = result.split(',')
        return result

__all__.append('JACOBTemperature')
class JACOBTemperature(Entity):
    def __init__(self,
                 cmd_str=None,
                 **kwargs):
        '''
        Args:
            cmd_str (str): query string to send to jacob
        '''
        Entity.__init__(self, **kwargs)
        if cmd_str is None:
            raise ThrowReply('service_error_invalid_value', '<base_str> is required to __init__ SimpleSCPIEntity instance')
        else:
            self.cmd_str = cmd_str
    """ Excerpt from JACOB documentation:
    The return type is String and contains 4 coma separated values.
    Example: 99270.000000,1.400050,11:41:46.816 06/13/2014,0
    99270.000000 = the resistance value in ohms for sensor #2
    1.400050 = the temperature in Kelvin for sensor #2
    11:41:46.816 06/13/2014 = the time the measurement was recorded
    0 = Status (See Status Summary)
    """

    @calibrate()
    def on_get(self):
        result=self.service.send_to_device(self.cmd_str)
        result = result.split(',')
        return result[1] # return the temperature in Kelvin

__all__.append('JACOBPressure')
class JACOBPressure(Entity):
    def __init__(self,
                 cmd_str=None,
                 **kwargs):
        '''
        Args:
            cmd_str (str): query string to send to jacob
        '''
        Entity.__init__(self, **kwargs)
        if cmd_str is None:
            raise ThrowReply('service_error_invalid_value', '<base_str> is required to __init__ SimpleSCPIEntity instance')
        else:
            self.cmd_str = cmd_str
    """ Example: readPressure(1) returns a string containing pressure data from the Jacob Gauge #1
    The return type is String and contains 4 coma separated values.
    Example: 8.502307,1005.326055,11:48:18.901 06/13/2014,0
    8.502307 = the pressure value in volts for gauge #1
    1005.326055 = the pressure in mbar for gauge #1
    11:48:18.901 06/13/2014 = the time the measurement was recorded
    0 = Status (See Status Summary
    """

    @calibrate()
    def on_get(self):
        result=self.service.send_to_device(self.cmd_str)
        result = result.split(',')
        return result[1] # return the pressure in mbar
    
__all__.append('JACOBFlow')
class JACOBFlow(Entity):
    def __init__(self,
                 cmd_str=None,
                 **kwargs):
        '''
        Args:
            cmd_str (str): query string to send to jacob
        '''
        Entity.__init__(self, **kwargs)
        if cmd_str is None:
            raise ThrowReply('service_error_invalid_value', '<base_str> is required to __init__ SimpleSCPIEntity instance')
        else:
            self.cmd_str = cmd_str
    """ he return type is String and contains 4 coma separated values.
    Example: 0.002454,0.490856,11:54:33.985 06/13/2014,0
    0.002454 = the flow value in volts from the flow meter
    0.490856 = the flow in uMoles/s from the flow meter
    11:54:33.985 06/13/2014 = the time the measurement was recorded
    0 = Status (See Status Summary
    """

    @calibrate()
    def on_get(self):
        result=self.service.send_to_device(self.cmd_str)
        result = result.split(',')
        return result[1] # return the flow in uMoles/s


__all__.append('JACOBService')
class JACOBService(Service):
    '''
    JACOBService is a class for communicating with the JACOB ethernet device using the dripline framework.
    '''
    def __init__(self,
                 socket_timeout=1.0,
                 socket_info=('localhost', 1234),
                 response_terminator=None,
                 reply_echo_cmd=False,
                 **kwargs
                 ):
        '''
        Args:
            socket_timeout (int): number of seconds to wait for a reply from the device before timeout.
            socket_info (tuple or string): either socket.socket.connect argument tuple, or string that
                parses into one.
            cmd_at_reconnect ([str,...]): a list of commands to send to the device every time the socket
                connection is estabilished note that these will be sent on *every* connection, which may be
                disruptive to ongoing activity.
            reconnect_test (str): expected return from the last command in the cmd_at_reconnect list, must
                match exactly or the reconnect is deemed a failure
            reply_echo_cmd (bool): indicates that the device includes the the received command in its reply

        '''
        Service.__init__(self, **kwargs)

        if isinstance(socket_info, str):
            logger.debug(f"Formatting socket_info: {socket_info}")
            re_str = "\([\"'](\S+)[\"'], ?(\d+)\)"
            (ip,port) = re.findall(re_str,socket_info)[0]
            socket_info = (ip,int(port))
        
        self.alock = threading.Lock()
        self.socket = socket.socket()
        self.socket_timeout = float(socket_timeout)
        self.socket_info = socket_info
        #self.cmd_at_reconnect = cmd_at_reconnect
        #self.reconnect_test = reconnect_test
        #self.command_terminator = command_terminator
        #self.response_terminator = response_terminator
        #self.reply_echo_cmd = reply_echo_cmd

        #I could keep these in a config file, but there is only 
        #one JACOB device, so I think it is ok to hardcode them here 
        #self.add_child(JACOBEntity(name="JACOB_last_error",cmd_str="getLastError()"))

        self._reconnect()

    def _reconnect(self):
        '''
        Method establishing socket to ethernet instrument.
        Called by __init__ or send (on failed communication).
        '''
        self.socket.close()
        self.socket = socket.socket()
        try:
            self.socket = socket.create_connection(self.socket_info, self.socket_timeout)
        except (socket.error, socket.timeout) as err:
            logger.warning(f"connection {self.socket_info} refused: {err}")
            raise ThrowReply('resource_error_connection', f"Unable to establish ethernet socket {self.socket_info}")
        logger.info(f"Ethernet socket {self.socket_info} established")
        # Shall I add a cmd at reconnect here?  I know of know 'operation complete' command

    def send_to_device(self, command, **kwargs):
        '''
        Standard device access method to communicate with instrument.
        NEVER RENAME THIS METHOD!

        command needs to just be a single string
        '''
        self.alock.acquire()

        try:
            data = self._send_command(command)
        except socket.error as err:
            logger.warning(f"socket.error <{err}> received, attempting reconnect")
            self._reconnect()
            data = self._send_command(command)
            logger.critical("Ethernet connection reestablished")
        # exceptions.DriplineHardwareResponselessError
        except Exception as err:
            logger.critical(str(err))
            try:
                self._reconnect()
                data = self._send_command(command)
                logger.critical("Query successful after ethernet connection recovered")
            except socket.error: # simply trying to make it possible to catch the error below
                logger.critical("Ethernet reconnect failed, dead socket")
                raise ThrowReply('resource_error_connection', "Broken ethernet socket")
            except Exception as err: ##TODO handle all exceptions, that seems questionable
                logger.critical("Query failed after successful ethernet socket reconnect")
                raise ThrowReply('resource_error_no_response', str(err))
        finally:
            self.alock.release()
        to_return =data
        logger.debug(f"should return:\n{to_return}")
        return to_return


    def _send_command(self, command):
        '''
        Take a single command, send to instrument and receive responses, do any necessary formatting.

        commands (str): command to send to instrument, should be a single string, not a list of strings
        '''
        length_bytes=len(command).to_bytes(4, byteorder = 'big')
        bytes_to_send=(length_bytes.decode() + command).encode()
        logger.debug(f"sending: {command.encode()}")
        self.socket.send(bytes_to_send)
        try:
            #read the length of the response
            lenstr=self.socket.recv(4)
            length=int.from_bytes(lenstr, byteorder = 'big')
            #then read that many bytes
            data=self.socket.recv(length).decode(errors='replace')
        except socket.timeout:
            logger.warning(f"socket.timeout condition met; received:\n{repr(data)}")
            raise ThrowReply('resource_error_no_response', "Timeout while waiting for a response from the instrument")
        logger.debug(repr(data))
        return data
