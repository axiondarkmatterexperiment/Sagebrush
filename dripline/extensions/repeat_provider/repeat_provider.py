# standard libs
import logging

# internal imports
import scarab
from _dripline.core import op_t, create_dripline_auth_spec, Core, DriplineConfig, Receiver, MsgRequest, MsgReply 
from dripline.core import Service, AlertConsumer, ThrowReply, ObjectCreator
import datetime

__all__ = []
logger = logging.getLogger(__name__)

__all__.append('RepeatProvider')
class RepeatProvider(Service):
    def __init__(self, repeat_target, **kwargs):
        self._repeat_target = repeat_target
        Service.__init__(self,**kwargs)


    def _send_request(self, msgop, specifier=None, payload=None, timeout_s=None, lockout_key=None):
        '''
        internal helper method to standardize sending request messages
        '''
        a_specifier = specifier if specifier is not None else ""
        timeout = float(timeout_s) if timeout_s is not None else 10.
        target = self._repeat_target
        logger.debug("has specifier")
        logger.debug(f"specifier is: {a_specifier} {target}")
        a_request = MsgRequest.create(payload=scarab.to_param(payload), msg_op=msgop, routing_key=target, specifier=a_specifier)
        a_request.lockout_key = lockout_key if lockout_key is not None else ""
        logger.debug(f"request is {a_request}")
        reply_pkg = self.send(a_request) #may not exist
        if not receive_reply.successful_send:
            raise DriplineError('unable to send request')
        result = self._receive_reply( reply_pkg, timeout )
        logger.critical("get result {result}")
        return result

    def _receive_reply(self, reply_pkg, timeout_s):
        '''
        internal helper method to standardize receiving reply messages
        '''
        sig_handler = scarab.SignalHandler()
        sig_handler.add_cancelable(self._receiver)
        result = self._receiver.wait_for_reply(reply_pkg, timeout_s * 1000) # receiver expects ms
        sig_handler.remove_cancelable(self._receiver)
        return result     
    
#class RepeatProvider(Core, ObjectCreator):
#
#
#    def __init__(self, repeat_target, make_connection=True, endpoints=None,
#                    add_endpoints_now=True, enable_scheduling=False, 
#                    broadcast_key='broadcast', loop_timeout_ms=1000,
#                     message_wait_ms=1000, heartbeat_interval_s=60,
#                     username=None, password=None, authentication_obj=None,
#                     dripline_mesh=None, **kwargs):
#        self._repeat_target = repeat_target
#        dripline_config = DriplineConfig().to_python()
#        if dripline_mesh is not None:
#            dripline_config.update(dripline_mesh)
#        if authentication_obj is not None:
#            auth = authentication_obj
#        else:
#            dl_auth_spec = create_dripline_auth_spec()
#            auth_args = {
#              'username': {} if username is None else username,
#              'password': {} if password is None else password,
#            }
#            dl_auth_spec.merge( scarab.to_param(auth_args) )
#            auth_spec = scarab.ParamNode()
#            auth_spec.add('dripline', dl_auth_spec)
#            logger.debug(f'Loading auth spec:\n{auth_spec}')
#            auth = scarab.Authentication()
#            auth.add_groups(auth_spec)
#            auth.process_spec()
#
#        Core.__init__(self, config=scarab.to_param(dripline_config), auth=auth)
#        self.loop_timeout_ms = loop_timeout_ms 
#        self._receiver = Receiver()
#        # Endpoints
#        self.endpoint_configs = endpoints
#        if( add_endpoints_now ):
#            self.add_endpoints_from_config()
#
#        if kwargs:
#            logger.debug(f'repeat_provider received some kwargs that it doesn\'t handle, which will be ignored: {kwargs}')
#    
#    def add_child(self,endpoint):
#        AlertConsumer.add_child(self, endpoint)
#
#    def add_endpoints_from_config(self):
#        if self.endpoint_configs is not None:
#            for an_endpoint_conf in self.endpoint_configs:
#                an_endpoint = self.create_object(an_endpoint_conf, 'Endpoint')
#                self.add_child( an_endpoint )
#                if getattr(an_endpoint, 'log_interval', datetime.timedelta(seconds=0)) > datetime.timedelta(seconds=0):
#                    logger.debug("queue up start logging for '{}'".format(an_endpoint.name))
#                    an_endpoint.start_logging()
#
#    def result_to_scarab_payload(self, result: str):
#        """
#        Intercept result values and throw error if scarab is unable to convert to param
#        TODO: Handles global Exception case, could be more specific
#        Args:
#            result (str): request message passed
#        """
#        try:
#            return scarab.to_param(result)
#        except Exception as e:
#            raise ThrowReply('service_error_bad_payload',
#                             f"{self.name} unable to convert result to scarab payload: {result}")
#
#
#    #def send_to_service():
#    #  if isinstance(commands, str):
#    #    commands = [commands]
#    #  try:
#    #    request = {,}
#    #    data = self._send_request(commands)
#    #  except:
#    #    raise ThrowReply('repeat provider did not work')
