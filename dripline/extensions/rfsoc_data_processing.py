import re # used for FormatEntity
import asteval
import yaml
import json
from dripline.core import Entity, calibrate, ThrowReply
import numpy as np
from sagebrush import rfsoc_fits as fitting
import logging

logger = logging.getLogger(__name__)

__all__ = ['RfsocDataProcessing']

_all_calibrations = []

class RfsocDataProcessing(Entity):

    def __init__(self,**kwargs):

        Entity.__init__(self, **kwargs)

    #@calibrate(_all_calibrations)

    def process_spectrum(self,string_spectrum,f_start,f_stop,transmission_amps,reflection_amps):
        
        spectrum = np.fromstring(string_spectrum,dtype=np.float64,sep=',')
        freqs = np.linspace(f_start,f_stop,len(spectrum))
        tone_indices = find_tones(spectrum)
        interpolated_spectrum = interpolate_spectrum(spectrum,tone_indices)

        tone_powers = spectrum[tone_indices] - interpolated_spectrum[tone_indices]
        tone_freqs = freqs[tone_indices]
        
        transmission_powers = tone_powers[::2]*transmission_amps
        transmission_freqs = tone_freqs[::2]
        reflection_powers = tone_powers[1::2]*reflection_amps
        reflection_freqs = tone_freqs[1::2]

        transmission_fit = fitting.fit_transmission(transmission_powers,transmission_freqs)
        reflection_fit = fitting.fit_reflection(reflection_powers,reflection_freqs)

        snr = tone_powers/interpolated_spectrum[tone_indices]
        

        



    def find_max(self,string_array):

        return str(np.max(np.fromstring(string_array,dtype=np.float64,sep=',')))

    def find_tones(self,spec,n_tones=40,window_len=10,tone_ratio_low=0,tone_ratio_high=20):
        
        spec_len = len(spec)
        tone_indices = []
        loops = 0

        while len(tone_indices) != n_tones and loops < 50:
            #tone_ratio is a guess for the snr threshold for the tones. This loops through
            #a tone search, adjusting the threshold until it finds n_tones. If there are actually
            #the correct number of tones, it should resolve much faster than 50 loops

            tone_indices = []
            loops+=1
            tone_ratio = (tone_ratio_high+tone_ratio_low)/2 # a guess for the ratio of the tone power to the noise power

            for i in np.arange(0,int(np.floor(spec_len-window_len)),window_len):

                subspec = spec[i:i+window_len]
                subspec_max = np.max(subspec)
                subspec_max_index = np.where(subspec == subspec_max)[0][0]
                subspec_avg = np.mean(subspec[subspec != subspec_max]) #masking the maximum value
                if subspec_max >= tone_ratio*subspec_avg:
                    tone_indices.append(i+subspec_max_index)
            if len(tone_indices)==n_tones:
                return np.array2string(np.array(tone_indices),threshold=10000,separator=',')
            elif len(tone_indices) > n_tones:
                tone_ratio_low = tone_ratio
            else:
                tone_ratio_high = tone_ratio


        return None

    def interpolate_spectrum(spectrum,tone_indices):
        interpolated_spectrum = np.copy(spectrum)
        for index in tone_indices:
            interpolated_spectrum[index]=(interpolated_spectrum[index-1]+interpolated_spectrum[index-1])/2
        return interpolated_spectrum
