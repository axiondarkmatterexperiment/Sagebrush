from dripline.core import ThrowReply, MsgReply, Service 
from _dripline.core import MsgRequest, Receiver, op_t
# import scarab
import numpy as np  # Required for SAG_Spec

import axion_waveform_lib  # Required for SAG_Spec
import logging
# import sys

logger = logging.getLogger(__name__)

__all__ = ['SAGCoordinator']

class SAGInterface(Service):
    def __init__(self,
                 extra_logs=None,
                 state_extra_logs=None,
                 sag_injection_sets=None,
                 enable_output_sets=None,
                 disable_output_sets=None,
                 update_waveform_sets=None,
                 sag_arb_waveform_name=None,
                 dummy_message_sets=None,
                 switch_endpoint=None,
                 **kwargs):
        super().__init__(**kwargs)

        # Safe defaults
        self.extra_logs = extra_logs or []
        self.state_extra_logs = state_extra_logs or {}
        self.sag_injection_sets = sag_injection_sets or []
        self.enable_output_sets = enable_output_sets or []
        self.disable_output_sets = disable_output_sets or []
        self.update_waveform_sets = update_waveform_sets or []
        self.sag_arb_waveform_name = sag_arb_waveform_name
        self.dummy_message_sets = dummy_message_sets or []
        self.switch_endpoint = switch_endpoint 
        self.evaluator = Interpreter()

    def _do_set_collection(self, these_sets, values):
     set_list = []
    # First parse all string evaluations, make sure they work
     for a_calculated_set in these_sets:
        self.logger.debug(f"Dealing with calculated_set: {a_calculated_set}")
        set_list.append(self._process_calculated_set(values, **a_calculated_set))

    # Now actually try to set things
        self.logger.debug(f"Set list: {set_list}")
        for this_endpoint, this_value in set_list:
         self.logger.info(f"Setting endpoint '{this_endpoint}' with value: {this_value}")
        self.provider.set(this_endpoint, this_value)
        raise ValueError('kwargs should only be a single dict')

    def _process_calculated_set(self, values, evaluate_statement=True, **kwargs):
        """Deals with any processing needed to evaluate a single set out of a set collection """
        if len(kwargs) != 1:
         raise dripline.core.DriplineValueError('kwargs should only be a single entry dict')

        [(this_endpoint, set_str)] = kwargs.items()
        self.logger.debug(f"trying to understand: {this_endpoint}->{set_str}")

        this_value = set_str
        if '{' in set_str and '}' in set_str:
             self.logger.debug(f"replacing from {set_str} with something from {values}")
        try:
            this_set = set_str.format(**values)
        except KeyError as e:
            raise dripline.core.DriplineValueError(
                f"required parameter, <{str(e)}>, not provided"
            )

        self.logger.debug(f"substitutions make that RHS = {this_set}")

        if evaluate_statement:
            this_value = self.evaluator(this_set)

            # Handle an evaluation error
            if len(self.evaluator.error) > 0:
                error_msg = 'Error in evaluating substituted value'
                for err in self.evaluator.error:
                    error_msg += f": ({err.get_error()[0]}) {err.get_error()[1]}"
                raise ValueError(error_msg)
        else:
            this_value = this_set

        self.logger.debug(f"or a set value of {this_value}")
        return (this_endpoint, this_value)
    
    def _do_extra_logs(self, sensors_list):
     ''' Send a scheduled_action (log) command to configured list of sensors (this is for making sure we log everything
    that should be recorded on each injection, but which is not already/automatically logged by a log_on_set action) '''
     self.logger.info(f"triggering logging of the following sensors: {sensors_list}")
     for a_sensor in sensors_list:
        self.provider.cmd(a_sensor, 'scheduled_action') 

    def update_state(self, new_state):
        # do universal extra logs
        self._do_extra_logs(self.extra_logs)
        # do state-specific extra logs
        if new_state in self.state_extra_logs:
            self._do_extra_logs(self.state_extra_logs[new_state])
        else:
            self.logger.warning('state <{}> does not have a state-specific extra logs list, please create one (it may be empty)'.format(new_state))
        # actually set to the new state
        if new_state == 'term':
            self.do_disable_output_sets()
            self.provider.set(self.switch_endpoint, "term")
        elif new_state == 'sag':
            self.do_enable_output_sets()
            self.provider.set(self.switch_endpoint, "sag")
        elif new_state == 'vna':
            # set the switch
            self.provider.set(self.switch_endpoint, "vna")
            # disable outputs
            self.do_disable_output_sets()
        elif new_state == 'locking':
            raise ValueError('locking state is not currently supported')
        else:
            raise ValueError("don't know how to set the SAG state to <{}>".format(new_state))
        
    def do_enable_output_sets(self):
         self.logger.info('enabling lo outputs')
         self._do_set_collection(self.enable_output_sets, {})

    def do_disable_output_sets(self):
        self.logger.info('disabling lo outputs')
        self._do_set_collection(self.disable_output_sets, {})
    
    def configure_injection(self, **parameters):
        '''
        parameters: (dict) - keyworded arguments are available to all sensors as named substitutions when calibrating
        '''
        self.logger.info('in configure injection')
        # to extra sets calculated from input parameters
        self._do_set_collection(self.sag_injection_sets, parameters)
        # set to state 'sag' (which enables output)
        self.update_state("sag")

    def update_waveform(self, **parameters):
        '''
        updates waveform of choice into the arb static memory slot of choice
        '''
        self.logger.info('in update waveform')
        self.f_rest = float(parameters['f_rest'])
        self.line_shape = str(parameters['shape_type'])
        self.sag_arb_waveform_name = str(parameters['arb_waveform_name'])
        self.send_thru_sag_arb_service = bool(parameters['use_sag_arb_service'])
        self.logger.info('send_thru_sag_arb_service set to {}'.format(self.send_thru_sag_arb_service))
    
    def SAG_Spec(self):
        """ This function generates the spectral distribution function of the axion waveform 
        due to the distribution of kinetic energy in the axion field as measured in the 
        experiment's laboratory frame (taken from the supplied keyword arguments to update_waveform).

        The length of entries in the power spectrum is half the length allowed by the arb, 
        so that the IFFT'd time series will be of the proper length. Similar story for 
        the bandwidth of the retrieved spectrum.

        Four line shapes are supported:
            max_2017       = N-body maxwellian form from Lentz et al. 2017
            big_flows      = Caustic ring flows (n=4?) from Pierre Sikivie halo model
            bose_nbody_2020= Bose N-body halo model from Lentz et al. 2020
            maxwellian     = isothermal sphere halo model form from Turner et al. 1990"""
        # initialize spectrum
        spec = np.zeros(self.N // 2)
        bandwidth = self.f_stan * (self.N - self.n) / 2

        # determine line shape
        ls = self.line_shape.lower()
        if any(word in ls for word in ["body", "2017", "max"]):
            line_shape = "n-body"
        elif any(word in ls for word in ["flow", "big", "sikivie"]):
            line_shape = "big flows"
        elif any(word in ls for word in ["bose", "entangled", "bec"]):
            line_shape = "bose_nbody_2020"
        else:
            line_shape = "SHM"  # default: maxwellian

        # get waveform spectrum
        aw = axion_waveform_lib.axion_waveform_sampler(
            line_shape=line_shape,
            f_rest=self.f_rest,
            f_spacing=self.f_stan,
            bandwidth=bandwidth)
        spec_short, freqs = aw.get_freq_spec()

        # place into spectrum array
        spec[-len(spec_short):] = spec_short
        self.spectrum = list(spec)

        return None
    def spectrum2Timeseries(self):
            '''
            This function takes the designated spectral function and converts it into a time series.
            As the input is a (power) spectral function is considered as the output of an FFT, 
            truncated for positive frequencies and then magnitude squared, we semi-invert this process
            by taking the square root of the PSF, give it a phase, conjugate-wise
            extend its range to positive and negative frequencies and perform an inverse FFT, which should be real valued.            
            '''
            N=self.N
            #print(N)
            sqrt_spectrum = np.sqrt(self.spectrum)
            phases = 0.0 #0.0 #np.random.uniform(low=0,high=2*np.pi,size=N)
            amplitudes_posf = (sqrt_spectrum*np.exp(1j*phases))
            amplitudes_negf = [np.conjugate(amp) for amp in amplitudes_posf]
            amps_conc = list(amplitudes_posf) + list(reversed(amplitudes_negf))
            self.tseries_long=np.fft.ifft(amps_conc)
            tseries = np.roll(self.tseries_long,self.N//2) # rolling highest amplitude region of time series to center to minimize discontinuities between endpoints
            print(len(tseries))

            self.re_tseries = list(tseries.real) # though it should be real already
            return None
    def reScale(self):
            '''
            this function rescales the tseries amplitude to -8191:8191
            '''
            maxVal=np.amax(self.re_tseries)
            minVal=np.amin(self.re_tseries)
            
            #print('maxVal='+str(maxVal))
            #print('minVal='+str(minVal))
            
            N=np.size(self.re_tseries)
            scale=np.zeros(N)
            #rescales amplitude to -8191:8191
            for i in range(0, N):
                scale[i]=int(round((16382*(self.re_tseries[i]-minVal)/(maxVal-minVal))-8191))
            
            self.scale = scale
            return None

    def writeWF(self):
            '''
            This function reads out the tscaled spectrum and returns all values of tscaled as a string
            '''
            self.scale = [int(number) for number in self.scale] # redundant to reScale, yes, but necessary for unknown reasons
            self.logger.info('waveform element numbers of type: '+str(type(self.scale[0])))
            self.msg="DATA:DAC VOLATILE, "
            self.WFstr = ""
            
            N=np.size(self.scale)
            
            for i in range(0, N):
                self.WFstr+=str(int(self.scale[i]))
                if i<N-1:
                    self.WFstr+=", "
            
            self.msg+=self.WFstr 
            self.msg+="\n"
            
            # also partitioning the waveform string into J parts
            J = 4
            K = N//(J-1)     
            self.WFsegs = {"sag_waveform_array_"+str(i): self.scale[i*K:(i+1)*K] for i in range(0,J)} 
            return None

    def writeToAG(self):
            '''
            TCP_IP = a string representing a hostname in Internet domain notation or an IPv4 address
            TCP_PORT = int
            '''
            self.logger.info('In writeToAG')
            TCP_IP='10.95.101.64'
            TCP_PORT=5025
            BUFFER_SIZE=1024

            s=skt.socket(skt.AF_INET, skt.SOCK_STREAM) #creating a new socket
            s.connect((TCP_IP, TCP_PORT)) #connect to a remote socket at address

            msg3=self.msg
            
            msg2="FREQ 50 \n" #set frequency [Hz]
            s.send(msg2.encode()) # message needs to be encoded as a byte string
            #resp = s.recv(BUFFER_SIZE)
            #logger.info(string(resp.decode()))
            
            s.send(msg3.encode()) #sends tscaled to the socket
            #resp = s.recv(BUFFER_SIZE)
            #logger.info(string(resp.decode()))
            
            #self.waveform_name = 'MY_AXION4'
            msg="DATA:COPY "+str(self.sag_arb_waveform_name)+"\n" #this saves the name of the line shape to long term memory
            s.send(msg.encode())
            #resp = s.recv(BUFFER_SIZE)
            #logger.info(string(resp.decode()))
            self.logger.info("messages passed to arb")
            s.close()
            return None
    def sendToAG(self):
            '''
            Iterates over messages to send to waveform generator to update line shape 
            '''
            self.logger.info('in send to AG')
            values = self.WFsegs
            self.logger.info('setting waveform array in '+str(len(values))+' segments: '+str(values))
            self.logger.info('update_waveform_sets: '+str(self.update_waveform_sets))
            self._do_set_collection(self.update_waveform_sets, values)
            self.logger.info('set complete')
            self.logger.info('pinging arb for current waveform stats')
            self.provider.cmd('sag_arb','retrieve_setting',value=[self.sag_arb_waveform_name],timeout=300)
            self.configure_injection
            self.logger.info('settings retrieved')
            self.logger.info('instructing sag_arb service to save waveform to {}'.format(self.sag_arb_waveform_name))
            self.provider.cmd('sag_arb','send_waveform',value=[self.sag_arb_waveform_name],timeout=300)
            self.logger.info('waveform sent')
            return None

    def run_waveform_pipeline(self):
        """  Execute the full waveform generation pipeline:
        1. Generate spectrum
        2. Convert to time series
        3. Rescale
        4. Write waveform
        5. Send to arb (if configured)    """
        self.SAG_Spec()
        self.spectrum2Timeseries()
        self.reScale()
        self.writeWF()

        if self.send_thru_sag_arb_service:
            self.sendToAG()
        else:
            self.writeToAG()

        return None
    def dummy_message(self, **parameters):
        """
        Method for sending dummy message N items long with entries b bits each to the sag arb service
        Will send both in stringified and list formats
        """
        self.logger.info('in dummy message')       
        b = int(parameters['b'])
        N = int(parameters['N'])
        Nlist = [2**b for i in range(N)]
        stringlist = ""
        for i,entry in enumerate(Nlist):
                stringlist+=str(int(entry))
                if i<N-1:
                    stringlist+=", "
        #print(stringlist)
        
        values = {"sag_dummy_message_0":stringlist}
        self.logger.info('sending dummy list string to SAG arb service')
        self._do_set_collection(self.dummy_message_sets, values)
        #self.provider.cmd('sag_arb','print_dummy_message',timeout=300)
        
        values = {"sag_dummy_message_0":Nlist}
        self.logger.info('sending explicit list to SAG arb service')
        self._do_set_collection(self.dummy_message_sets, values)
        #self.provider.cmd('sag_arb','print_dummy_message',timeout=300)
        return None



