import re # used for FormatEntity
import asteval
import yaml
import json
from dripline.core import Entity, calibrate, ThrowReply
import numpy as np
from scipy.signal import savgol_filter
from sagebrush import rfsoc_fits as fitting
import logging

logger = logging.getLogger(__name__)

__all__ = ['RfsocDataProcessing']

_all_calibrations = []

class RfsocDataProcessing(Entity):

    def __init__(self,**kwargs):

        Entity.__init__(self, **kwargs)

    #@calibrate(_all_calibrations)

    def process_spectrum(self,json_args):

        args = json.loads(json_args)

        spectrum = np.fromstring(args["string_spectrum"],dtype=np.float64,sep=',')
        transmission_amps = np.fromstring(args["transmission_amps_str"],dtype=np.float64,sep=',')
        reflection_amps = np.fromstring(args["reflection_amps_str"],dtype=np.float64,sep=',')
        freqs = np.linspace(args["f_start"],args["f_stop"],len(spectrum))
        options = json.loads(args["options_str"])
        options["frequencies"]=freqs

        output = {"Error":"False"}

        #find and return indices of transmission and reflection tones. Options is a dict of arguments
        #that specifies the method of searching for these tones and deciphering which is a 
        # reflection/transmission tone
        try:
            transmission_tone_indices,reflection_tone_indices = self.find_tones_options(spectrum,options)
        except ValueError as e:
            return json.dumps({"Error":"True","Code":e},separators=(",",":"))

        #interpolate tones to get raw power spectrum
        tone_indices = np.sort(np.concatenate((transmission_tone_indices,reflection_tone_indices)))
        interpolated_spectrum = self.interpolate_spectrum(spectrum,tone_indices)
        interpolated_spectrum_fit = savgol_filter(interpolated_spectrum,window_length=50,polyorder=2)
        output["interpolated_spec"] = np.array2string(interpolated_spectrum,separator=",",threshold=10000,max_line_width=np.inf)[1:-1]

        #find tone powers with noise power subtracted
        transmission_tone_powers = spectrum[transmission_tone_indices] - interpolated_spectrum_fit[transmission_tone_indices]
        reflection_tone_powers = spectrum[reflection_tone_indices] - interpolated_spectrum_fit[reflection_tone_indices]
        tone_powers = spectrum[tone_indices] - interpolated_spectrum_fit[tone_indices]
        output["TP"] = np.array2string(transmission_tone_powers,separator=",",threshold=1000,max_line_width=np.inf)[1:-1]
        output["RP"] = np.array2string(reflection_tone_powers,separator=",",threshold=1000,max_line_width=np.inf)[1:-1]
        
        #find transmission/reflection scattering parameters
        transmission_powers = transmission_tone_powers/(transmission_amps**2)
        transmission_freqs = freqs[transmission_tone_indices]
        reflection_powers = reflection_tone_powers/(reflection_amps**2)
        reflection_freqs = freqs[reflection_tone_indices]

        #try fit on the transmission/reflection scattering parameters
        try:
            if options["JPA_state"] == "Off":
                transmission_fit = fitting.transmission_fit_options(transmission_powers,transmission_freqs,"cavity")
                reflection_fit = fitting.reflection_fit_options(reflection_powers,reflection_freqs,"cavity")
                output["TN"]=transmission_fit[0]
                output["TF0"]=transmission_fit[1]
                output["TQ"]=transmission_fit[2]
                output["RN"]=reflection_fit[0]
                output["RF0"]=reflection_fit[1]
                output["RQ"]=reflection_fit[2]
            elif options["JPA_state"] == "On":
                transmission_fit = fitting.transmission_fit_options(transmission_powers,transmission_freqs,"jpa")
                reflection_fit = fitting.reflection_fit_options(reflection_powers,reflection_freqs,"jpa")
                output["TN"]=transmission_fit[0]
                output["TF0"]=transmission_fit[1]
                output["TQ"]=transmission_fit[2]
                output["TFJPA"]=transmission_fit[3]
                output["TQJPA"]=transmission_fit[4]
                output["RN"]=reflection_fit[0]
                output["RF0"]=reflection_fit[1]
                output["RQ"]=reflection_fit[2]
                output["RFJPA"]=reflection_fit[3]
                output["RQJPA"]=reflection_fit[4]
            else:
                return json.dumps({"Error":"True","Code":"Unrecognized JPA_state"})
            
        except ValueError as e:
            return json.dumps({"Error":"True","Code":e},separators=(",",":"))


        snr = tone_powers/interpolated_spectrum_fit[tone_indices]
        output["SNR"]=np.array2string(snr,separator=",",threshold=1000,max_line_width=np.inf)[1:-1]

        #If JPA is off, find how amplitudes need to be adjusted. Returned is a ratio for what the new amplitudes should be compared to the old amplitudes
        if options["JPA_state"] == "Off":
            transmission_snr = transmission_tone_powers/interpolated_spectrum_fit[transmission_tone_indices]
            reflection_snr = reflection_tone_powers/interpolated_spectrum_fit[reflection_tone_indices]
            new_transmission_amps = np.min(np.array([np.sqrt(50/(transmission_snr+40)),np.ones(len(transmission_snr))]),axis=0) #the 50/(snr+40) is meant to keep the amplitudes near an snr of 10 without overcorrecting each cycle
            new_reflection_amps = np.min(np.array([np.sqrt(50/(reflection_snr+40)),np.ones(len(reflection_snr))]),axis=0)
            output["TA"]=np.array2string(new_transmission_amps,separator=",",threshold=1000,max_line_width=np.inf)[1:-1]
            output["RA"]=np.array2string(new_reflection_amps,separator=",",threshold=1000,max_line_width=np.inf)[1:-1]

        return json.dumps(output,separators=(",",":"))

    def find_tones_options(self,spec,options):
        if options["search_method"] == "prominence":
            tone_indices = self.find_tones_prominence(spec,options["n_tones"],options["window_len"],options["tone_ratio_low"],options["tone_ratio_high"])
            return tone_indices[::2],tone_indices[1::2]
        elif options["search_method"] == "frequency":
            return self.find_tones_frequency(spec,options["frequencies"],options["transmission_frequencies"],options["reflection_frequencies"],options["window_size"])

        raise ValueError("Tone search method not implemented")
    
    def find_tones_frequencies(self,spec,frequencies,transmission_frequencies,reflection_frequencies,window_size):

        transmission_bins = np.floor((transmission_frequencies-frequencies[0])/(frequencies[1]-frequencies[0]),dtype=np.int32)
        transmission_bins = transmission_bins[transmission_bins>window_size/2 and transmission_bins < len(spec)-window_size/2]

        reflection_bins = np.floor((reflection_frequencies-frequencies[0])/(frequencies[1]-frequencies[0]),dtype=np.int32)
        reflection_bins = reflection_bins[reflection_bins>window_size/2 and reflection_bins < len(spec)-window_size/2]

        transmission_indices = np.zeros(len(transmission_bins))
        for index,bin in enumerate(transmission_bins,start=0):
            subspec = spec[bin-window_size/2:bin+window_size/2]
            subspec_max_index = np.where(subspec == np.max(subspec))[0][0]
            transmission_indices[index] = subspec_max_index

        reflection_indices = np.zeros(len(reflection_bins))
        for index,bin in enumerate(reflection_bins,start=0):
            subspec = spec[bin-window_size/2:bin+window_size/2]
            subspec_max_index = np.where(subspec == np.max(subspec))[0][0]
            reflection_indices[index] = subspec_max_index

        return transmission_indices,reflection_indices

    def find_tones_prominence(self,spec,n_tones=40,window_len=10,tone_ratio_low=0,tone_ratio_high=30):

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
                return np.array(tone_indices)
            elif len(tone_indices) > n_tones:
                tone_ratio_low = tone_ratio
            else:
                tone_ratio_high = tone_ratio

        raise ValueError("Could not find {} tones".format(n_tones))

    def interpolate_spectrum(self,spectrum,tone_indices):
        interpolated_spectrum = np.copy(spectrum)
        for index in tone_indices:
            interpolated_spectrum[index]=(interpolated_spectrum[index-1]+interpolated_spectrum[index-1])/2
        return interpolated_spectrum
