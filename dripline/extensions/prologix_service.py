from dripline.core import ThrowReply, MsgReply, Service 
from _dripline.core import MsgRequest, Receiver, op_t
import scarab
import logging
import sys

logger = logging.getLogger(__name__)

__all__ = ['SagPrologixService']

class SagPrologixService(Service):
    def __init__(self, address, routing, message_wait_ms = 2000,response_terminator=None, **kwargs):
        Service.__init__(self, **kwargs)
        self.addr = address 
        self.repeat_routing_key = routing
        self._message_wait_ms = message_wait_ms
        self.response_terminator = response_terminator

    def send_to_device(self, cmd, **kwargs):
        cmd = cmd[0]
        # Construct the full GPIB command
        to_send = [f'++addr {self.addr}\r++addr', cmd]
        payload = {'commands': to_send}

        # Create message request
        request = MsgRequest.create(scarab.to_param(payload), op_t.cmd, self.repeat_routing_key,specifier='send_to_device')  

        # Send request
        receiver = Receiver()
        reply_pkg = self.send(request)
        if not reply_pkg.successful_send:
            raise ThrowReply("Failed to send command to Prologix GPIB device.")

        # Handle response
        sig_handler = scarab.SignalHandler()
        sig_handler.add_cancelable(receiver)
        result = receiver.wait_for_reply(reply_pkg, self._message_wait_ms)  # timeout in ms
        sig_handler.remove_cancelable(receiver)

        #logger.debug(f"raw result:\n{(result)}\n response {response}")
        response = str(getattr(result,'payload'))

        # Split and process
        split_result=response.split(";")
        addr = split_result[0]
        result_str = split_result[1]
        logger.debug(f'{split_result}')

        # Trim terminators
        if self.response_terminator:
            if addr.endswith(self.response_terminator):
                addr = addr[:-len(self.response_terminator)]
                logger.debug(f"GPIB address check trimmed to {addr}")
            if result_str.endswith(self.response_terminator):
                result_str = result_str[:-len(self.response_terminator)]
                logger.debug(f"result trimmed to {result_str}")

        # Address mismatch check
        if int(addr) != self.addr:
            raise ThrowReply("Unable to set GPIB address at Prologix")

        logger.debug(f"instrument got back: {result_str}")
        return result_str
