import pyModbusTCP.client
from dripline.core import Service, ThrowReply


import logging
logger = logging.getLogger(__name__)

__all__ = []

__all__.append('ModbusService')
class ModbusService(Service):
    def __init__(self,
                 modbus_host=None,
                 modbus_port=502,
                 **kwargs):
        Service.__init__(self,**kwargs)
        if modbus_host is None:
            raise ThrowReply("modbus_host is a required configuration parameter for <modbus_service>")
        self.modbus_client = pyModbusTCP.client.ModbusClient(host=modbus_host, port=modbus_port, auto_open=True)

    def read_holding(self, register, n_registers):
        logger.debug('calling read_holding_registers({}, {})'.format(register, n_registers))
        return self.modbus_client.read_holding_registers(register, n_registers)
