import math
import numpy as np
import cmath
from scipy.optimize import least_squares
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy import stats

__all__ = []

def iq_packed2powers(iq_data):
    """Turn iq data in [r,i,r,i,r,i...] format into an array of powers"""
    powers = np.zeros(int(len(iq_data)/2))
    for i in range(int(len(iq_data)/2)):
        powers[i] = iq_data[2*i]*iq_data[2*i]+iq_data[2*i+1]*iq_data[2*i+1]
    return powers


def unpack_iq_data(iq_data):
    """takes iq data in [r,i,r,i,r,i] format and unpacks into two
    arrays [r,r,r],[i,i,i]"""
    ret_r = np.zeros(len(iq_data)//2)
    ret_i = np.zeros(len(iq_data)//2)
    for i in range(0, len(iq_data), 2):
        ret_r[i//2] = iq_data[i]
        ret_i[i//2] = iq_data[i+1]
    return ret_r, ret_i


def repack_iq_data(data_r, data_i):
    """takes iq data seperated into 2 arrays [r,r,r], [i,i,i] and
    combines them into one array [r,i,r,i,r,i]."""
    if not (data_r.size == data_i.size):
        raise ValueError("Real and imaginary vectors should be the same length")
    iq_series = np.empty((data_r.size + data_i.size,), dtype=data_r.dtype)
    iq_series[0::2] = data_r
    iq_series[1::2] = data_i
    return iq_series


def find_nearest_idx(array, value):
    """Finds the index of an array element that is closest to specified
    value"""
    # TODO figure out what to do with symmetric functions.
    idx = (np.abs(array-value)).argmin()
    return idx


def sc_guess_fo(f, Gamma2, measurement_type):
    """Guesses the resonant frequency"""
    if measurement_type == "reflection":
        ind_fo = np.argmin(Gamma2)  # find index of resonant frequency
    elif measurement_type == "transmission":
        ind_fo = np.argmax(Gamma2)  # find index of resonant frequency
    else:
        raise Exception("not a valid measurement type")
    return f[ind_fo]


def sc_guess_offset(y, measurement_type):
    """Gueses normalization for reflection fit."""
    filt_perc = 0.33
    # cut out bottom low_filt_perc of y values. Basically want to filter
    # out the notch a bit.
    if measurement_type == "reflection":
        y_filtered = stats.trim1(y, filt_perc, tail='left')
    elif measurement_type == "transmission":
        y_filtered = stats.trim1(y, filt_perc, tail='right')
    else:
        raise Exception("not a valid measurement type")
    return np.median(y_filtered)


def sc_guess_dy(y, measurement_type):
    """Returns a guess for the depth of the Lorentzian. The depth is always a positive number"""
    if measurement_type == "reflection":
        depth = sc_guess_offset(y, measurement_type) - np.min(y)
    elif measurement_type == "transmission":
        depth = np.max(y) - sc_guess_offset(y, measurement_type)
    else:
        raise Exception("not a valid measurement type")
    return depth


def sc_guess_q(f, y, measurement_type):
    """Returns a guess for the Q of the Lorentzian"""

    # find index of resonant frequency
    if measurement_type=="reflection":
        ind_fc = np.argmin(y)  
    elif measurement_type=="transmission":
        ind_fc = np.argmax(y)  
    else:
        raise Exception("not a valid measurement type")
    fc = f[ind_fc]  # obtain resonant frequency

    # look at the left of the resonance
    dy = sc_guess_dy(y, measurement_type)
    C = sc_guess_offset(y, measurement_type)
    left_y = y[:ind_fc]
    if measurement_type=="reflection":
        ind_fwhm = find_nearest_idx(left_y, C-dy/2)
    elif measurement_type=="transmission":
        ind_fwhm = find_nearest_idx(left_y, C+dy/2)
    else:
        ind_fwhm = find_nearest_idx(left_y, C+dy/2)
        raise Exception("not a valid measurement type")

    # fend distance between fwhm and resonance
    f1 = f[ind_fwhm]
    # guess bandwidth as twice that distance
    del_f = 2*(fc-f1)
    Q_guess = fc/del_f
    return Q_guess


def sc_guess_fit_params(f, power, measurement_type):
    """Finds an initial guess for the fittings parameters of reflected
    power"""
    fo_guess = sc_guess_fo(f, power, measurement_type)
    Q_guess = sc_guess_q(f, power, measurement_type)
    dy_guess = sc_guess_dy(power, measurement_type)
    C_guess = sc_guess_offset(power, measurement_type)
    return fo_guess, Q_guess, dy_guess, C_guess


def func_sc_pow_reflected(f, fo, Q, del_y, C):
    """The reflected power. Just a Lorentzian"""
    if del_y>C: return 0 ## Temp fix
    return -(fo/(2*Q))**2*del_y/((f-fo)**2+(fo/(2*Q))**2)+C

def func_sc_pow_transmitted(f, fo, Q, del_y, C):
    """The reflected power. Just a Lorentzian"""
    return (fo/(2*Q))**2*del_y/((f-fo)**2+(fo/(2*Q))**2)+C


def get_arr_ends(x, n_end_elements):
    """returns the first and last n_end_elements of array x"""
    return np.concatenate([x[:n_end_elements], x[-n_end_elements:]])


def sc_reflection_deconvolve_line(f, Gamma_mag, Gamma_phase, C_fit):
    """Finds the reflection coefficient off of the cavity by deconvolving
    the line path"""
    Gamma_cav_mag = Gamma_mag*np.sqrt(1/C_fit)

    interp_phase = interp1d(f, Gamma_phase, kind='cubic')
    f_ends = get_arr_ends(f, 5)
    phase_ends = get_arr_ends(Gamma_phase, 5)
    interp_phase_wo_notch = np.poly1d(np.polyfit(f_ends, phase_ends, 1))
    delay_phase = interp_phase_wo_notch(f)
    Gamma_cav_phase = interp_phase(f) - delay_phase

    return Gamma_cav_mag, Gamma_cav_phase


def sc_calculate_coupling(mag_fo, phase_fo):
    """Calculate coupling to a cavity after reflection fit is done"""
    # sgn = np.sign(phase_fo - np.pi) 
    sgn = np.sign(phase_fo)
    beta = (1+sgn*mag_fo)/(1-sgn*mag_fo)
    return beta


def sc_estimate_power_uncertainty(power):
    """Assume sqrt (like counting experiment)"""
    sig_power = np.sqrt(power)
    return sig_power

def calc_red_chisq(x, y, sigma_y, func, fit_param):
    """Calculates the reduced chi-square"""
    resid = y-func(x, *fit_param)
    chisq = np.sum(resid/sigma_y)
    dof = len(y)-len(fit_param)
    red_chisq = chisq/dof
    return red_chisq


def sc_reflection_fit_shape_database_hack(x, func, fit_param):
    """This takes the sidecar fit, which is in power, and returns it into the
    fit shape that the database expects. It expects iq series [r,i,r,i....]"""
    Gamma_mag = np.sqrt(func(x, *fit_param))

    Gamma_dummy = np.zeros_like(Gamma_mag)
    fit_shape = repack_iq_data(Gamma_mag, Gamma_dummy)
    return fit_shape


def transmission_power_shape(f, norm, f0, Q, noise):
    """returns the expected power from a transmission measurement at frequency f with parameters
        f0 - resonant frequency
        Q - resonant quality
        norm - normalization of the resonance
        noise - estimate of the noise background"""
    delta=Q*(f-f0)/f0
    return norm*(1/(1+4*delta*delta)+noise)


def reflection_iq_shape(f,norm,phase,f0,Q,beta,delay_time):
    """returns the expected [i,q] values from a reflection measurement
        """
#beta=2*atan(beta)/3.14159+1.0 only if we have trouble keeping beta within bounds
    delta=Q*(f-f0)/f0
    denom=1/(1+4*delta*delta)
    response=norm*complex(denom*((beta-1)-4*delta*delta),-denom*2*beta*delta)
    phase=cmath.exp(complex(0,phase+delay_time*(f-f0)))
    return response*phase


def reflection_iq_shape_their(f,norm,phase,f0,Q,beta,delay_time):
    """returns the expected [i,q] values from a reflection measurement
         """
    Q_0 = Q*(1.+beta) ## Convert to Unloaded Q-factor (Q_0) from Loaded Q-factor (Q)
    delta=Q_0*(f-f0)/f0
    phase=np.exp(1.j*(phase+delay_time*(f-f0)))
    return norm*phase*(beta-1.-1.j*(2.*delta))/(beta+1.+1.j*(2.*delta))


def fit_transmission(powers,frequencies):
    """
        Performs a least-squares fit on a transmission measurement, an array of powers and frequencies
        ASSUMPTIONS: (these go in as priors)
        - center frequency is within band
        - band is 1-10 
        - noise is the mean value of outer 10% of band
        - uncertainty is standard devation of outer 10% of band
    """
    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    f0_guess=frequencies[np.argmax(powers)]
    f_band=frequencies[-1]-frequencies[0]
    norm_guess=max(powers)
    Q_min=f0_guess/f_band
    if min(powers)/max(powers) < 0.02:
        # Empirical guess. Creates better fits for low-response measurements
        Q_max=50*Q_min 
    else:
        Q_max=20*Q_min
    Q_guess=0.5*(Q_max+Q_min)
    ten_percent_mark=int(math.ceil(0.1*len(frequencies)))
    noise_guess=0.5*(np.mean(powers[0:ten_percent_mark]+np.mean(powers[len(powers)-ten_percent_mark:len(powers)])))/norm_guess
    uncertainty=0.5*(np.std(powers[0:ten_percent_mark]+np.std(powers[len(powers)-ten_percent_mark:len(powers)])))
    if min(powers)/max(powers) < 0.02:
        # Relaxes search space. Better fits for low-response measurements
        noise_guess = 0.1*noise_guess
        uncertainty = 10*uncertainty
    norm_guess=max(powers)-noise_guess
    p0=[norm_guess,f0_guess,Q_guess,noise_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=3
        norm=x[0]
        f0=x[1]
        Q=x[2]
        noise=x[3]
        resid=np.zeros(nfreq+npriors)
        #add priors
        #Prior 1: frequency must be within bounds
        if f0<frequencies[0]:
            resid[nfreq]=(f0-frequencies[0])/f0_guess
            f0=frequencies[0]
        if f0>frequencies[-1]:
            resid[nfreq]=(frequencies[-1]-f0)/f0_guess
            f0=frequencies[-1]
        #Prior 2: Q must be neither too small nor too large
        if Q<Q_min:
            resid[nfreq+1]=10*nfreq*(Q-Q_min)/Q_min
            Q=Q_min
        if Q>Q_max:
            resid[nfreq+1]=10*nfreq*(Q_max-Q)/Q_min
            Q=Q_max
        #Prior 3: noise level not too big
        if noise<0:
            resid[nfreq+2]=-10*nfreq*noise
            noise=0
        if noise>0.1:
            resid[nfreq+2]=(noise-0.1)
            #note I do not clamp noise, it is possible it gets this high, just undesirable
        for i in range(nfreq):
            yp=transmission_power_shape(frequencies[i],norm,f0,Q,noise)
            resid[i]=(yp-powers[i])/uncertainty
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape=[ transmission_power_shape(f,res.x[0],res.x[1],res.x[2],res.x[3]) for f in frequencies ]

    #return norm,f0,Q,noise, chi square, fit shape
    to_return = {}
    to_return["fit_norm"] = res.x[0]
    to_return["fit_f0"] = res.x[1]
    to_return["fit_Q"] = res.x[2]
    to_return["fit_noise"] = res.x[3]
    to_return["fit_chisq"] = chisq
    to_return["fit_shape"] = fit_shape
    return to_return


def fit_reflection(iq_data,frequencies):
    """
        Performs a least-squares fit on a reflection measurement, an array of powers and frequencies
        ASSUMPTIONS: (these go in as priors)
        - center frequency is within band
        - NA band is 1-10 times q width
        - the phase from line length does not wrap around within the band
        - uncertainty is standard devation of outer 10% of band
    """
    if 2*len(frequencies)!=len(iq_data):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    powers=iq_packed2powers(iq_data)
    min_loc=np.argmin(powers)
    f0_guess=frequencies[min_loc]
    f_band=frequencies[-1]-frequencies[0]
    norm_guess=np.sqrt(max(powers))
    Q_min=f0_guess/f_band
    Q_max=100*Q_min
    Q_guess=0.5*(Q_max+Q_min)
    print("Q_min {} Q_max {}".format(Q_min,Q_max))
    beta_guess=1.0
    ten_percent_mark=int(math.ceil(0.1*len(frequencies)))

    power_mean=0.5*(np.mean(powers[0:ten_percent_mark]+np.mean(powers[len(powers)-ten_percent_mark:len(powers)])))
    power_stdev=0.5*(np.std(np.concatenate([powers[0:ten_percent_mark],powers[len(powers)-ten_percent_mark:len(powers)]])))
    uncertainty=power_stdev/(2*np.sqrt(power_mean))
    dip_depth=powers[min_loc]/(power_mean)
    #make a guess at the overall phase and phase slope of the whole thing
    left_phase=complex(-iq_data[0],-iq_data[1])
    right_phase=complex(-iq_data[-2],-iq_data[-1])
    phase_guess= cmath.phase(left_phase+ right_phase)
    # delay_time_guess=-(cmath.phase(right_phase)-cmath.phase(left_phase))/f_band
    delay_time_guess=0
    p0=[norm_guess,phase_guess,f0_guess,Q_guess,beta_guess,delay_time_guess]
    print("p0 is {}".format(p0))
    def fit_fcn(freqs,norm,phase,f0,Q,beta,delay_time):
       yp=reflection_iq_shape_their(freqs,norm,phase,f0,Q,beta,delay_time)
       yfit = repack_iq_data(np.real(yp),np.imag(yp))
       return yfit
    bnd = ((0,-np.pi,frequencies[0], Q_min, 0, -5e-5),(np.inf,np.pi,frequencies[-1], Q_max, 10., 5e-5))
    ##bound for [norm_guess,phase_guess,f0_guess,Q_guess,beta_guess,delay_time_guess]
    #-3.15 to 3.15 constraint the phase; 3e-5 for delay_time means O(1)km distance
    par, pcov = curve_fit(fit_fcn,xdata = frequencies, ydata = iq_data, p0 =  p0, bounds = bnd, sigma = uncertainty*np.ones(len(iq_data)))
    
    #calculate shape
    fit_shape = fit_fcn(frequencies,*par) 
    #fit_shape = fit_fcn(frequencies,*par) 
    chisq=sum(np.power(np.abs(fit_shape-np.array(iq_data))/uncertainty,2))/len(frequencies)
    
    # return
    to_return = {}
    to_return["fit_norm"] = par[0]
    to_return["fit_phase"] = par[1]
    to_return["fit_f0"] = par[2]
    to_return["fit_Q"] = par[3]
    to_return["fit_beta"] = par[4]
    to_return["fit_delay_time"] = par[5]
    to_return["fit_chisq"] = chisq
    to_return["fit_shape"] = list(fit_shape)
    to_return["dip_depth"] = dip_depth
    return to_return

def sidecar_fit_transmission(powers, frequencies, logger):
    """fits sidecar reflection data. For now, it is separate function from 
    the main experiment so as not to disturb it.
    Gamma is the measured reflection coefficient"""

    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    sig_powers = sc_estimate_power_uncertainty(powers)
    po_guess = sc_guess_fit_params(frequencies, powers, "transmission")

    pow_fit_param, pow_fit_cov = curve_fit(func_sc_pow_transmitted, frequencies,
                                           powers, p0=po_guess,
                                           sigma=sig_powers)

    fo_fit, Q_fit, del_y_fit, C_fit = pow_fit_param

    red_chisq = calc_red_chisq(frequencies, powers, sig_powers,
                               func_sc_pow_transmitted, pow_fit_param)

    fit_shape = func_sc_pow_transmitted(frequencies, *pow_fit_param)

    logger.info("fit norm {}".format(del_y_fit))
    logger.info("f0 fit {}".format(fo_fit))
    logger.info("Q fit {}".format(Q_fit))
    logger.info("Background level {}".format(C_fit))
    logger.info("reduced chi-square {}".format(red_chisq))

    # turn numpy arrays to lists so that json can iterate through it.
    # apparently, json can't deal with numpy objects, even if they are just a
    # single number. I don't know.
    fit_shape = fit_shape.tolist()

    return [del_y_fit, fo_fit, Q_fit, C_fit, red_chisq, fit_shape]


def search_sign(f0,frequencies,phases):
    idx=np.argmin(abs(frequencies-f0))
    if sum(phases[idx:idx+5]) < sum(phases[idx-5:idx]):
        return 1
    else:
        return -1
    
def sidecar_fit_reflection(iq_data, frequencies, logger):
    """fits sidecar reflection data. For now, it is separate function from 
    the main experiment so as not to disturb it.
    Gamma is the measured reflection coefficient"""
    # TODO Estimate uncertainty appropriately

    # # TODO change powers to an existing variable
    # if 2*len(frequencies)!=len(iq_data):
    #     raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies), len(powers)))
    # if len(frequencies) < 16:
    #     raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    Gamma_r, Gamma_i = unpack_iq_data(iq_data)
    Gamma_complex = Gamma_r+Gamma_i*1j
    Gamma_mag_sq = Gamma_r**2 + Gamma_i**2
    sig_Gamma_mag_sq = sc_estimate_power_uncertainty(Gamma_mag_sq)
    Gamma_mag = np.sqrt(Gamma_mag_sq)
    Gamma_phase = np.unwrap(np.angle(Gamma_complex))

    po_guess = sc_guess_fit_params(frequencies, Gamma_mag_sq, "reflection")

    pow_fit_param, pow_fit_cov = curve_fit(func_sc_pow_reflected, frequencies,
                                           Gamma_mag_sq, p0=po_guess,
                                           sigma=sig_Gamma_mag_sq)
    
    fo_fit, Q_fit, del_y_fit, C_fit = pow_fit_param

    red_chisq = calc_red_chisq(frequencies, Gamma_mag_sq, sig_Gamma_mag_sq,
                               func_sc_pow_reflected, pow_fit_param)
    
    
    
        # Gam_c is reflection coeffient Gamma of the cavity
    Gam_c_mag, Gam_c_phase = sc_reflection_deconvolve_line(frequencies, Gamma_mag, 
                                                           Gamma_phase, C_fit)
    # Calculates magnitude of Gamma_cavity by plugging resonant frequency into
    # fitted function
    Gam_c_mag_fo = np.sqrt(func_sc_pow_reflected(fo_fit, *pow_fit_param)*1/C_fit)
    
    Gam_c_interp_phase = interp1d(frequencies, Gam_c_phase, kind='cubic')

    # calculate phase of Gamma_cavity at resonant frequency by interpolating
    # data.
    Gam_c_phase_fo = Gam_c_interp_phase(fo_fit)

    sign_phase = search_sign(fo_fit,frequencies,Gam_c_phase)
    
    beta = sc_calculate_coupling(Gam_c_mag_fo, sign_phase)#Gam_c_phase_fo)
    
    # I don't get a delay time through this analysis. Just setting to -1 so I 
    # can match Gray's database.
    delay_time = -1 

    fit_shape = sc_reflection_fit_shape_database_hack(frequencies, func_sc_pow_reflected,
                                        pow_fit_param)

    dip_depth = np.sqrt(del_y_fit)
    
    logger.info("norm {}".format(C_fit))
    logger.info("phase {}".format(Gam_c_phase_fo))
    logger.info("f0 fit {}".format(fo_fit))
    logger.info("Q fit {}".format(Q_fit))
    logger.info("beta fit {}".format(beta))
    logger.info("reduced chi-square {}".format(red_chisq))
    logger.info("dip depth {}".format(dip_depth))

    # turn numpy arrays to lists so that json can iterate through it.
    # apparently, json can't deal with numpy objects, even if they are just a
    # single number. I don't know.
    Gam_c_phase_fo_from_interp = Gam_c_phase_fo.tolist() 
    fit_shape = fit_shape.tolist()

    return [C_fit, Gam_c_phase_fo_from_interp, fo_fit, Q_fit, beta,
            delay_time, red_chisq, fit_shape, dip_depth]

def find_peaks(vec,fraction,start,stop):
#examine the fraction*number top values in vec and return an array contiguous sections
#which are centroids of clusters interpolated between start and stop
    count=int(math.floor(fraction*len(vec)))
    vec=np.array(vec)
    max_indices=vec.argsort()[-count:]
    sorted_max_indices=sorted(max_indices)

    peak_centroids=[]
    last_num=sorted_max_indices[0]
    peak_start=last_num
    for i in range(1,len(sorted_max_indices)):
        if sorted_max_indices[i]!=(last_num+1): #part of this peak
            peak_centroids.append(int(0.5*( peak_start+sorted_max_indices[i-1])))
            peak_start=sorted_max_indices[i]
        last_num=sorted_max_indices[i]
    peak_centroids.append(int(0.5*( peak_start+sorted_max_indices[-1])))
    return np.interp(peak_centroids,[0,len(vec)],[start,stop])


def fit_na_log(log_entry):
    if type(log_entry) is dict:
        # Process like a tabular database entry
        row_index = 1 # Should be 3 rows. 1st row is formatting; last row is metadata
        fftkey = log_entry.keys()[4]
        iqdata = log_entry[fftkey][row_index]
        iqdata = (iqdata.split("{")[1]).split("}")[0]
        iqdata = [float(x) for x in iqdata.split(",")]

        namekey = log_entry.keys()[6]
        measurement_type = log_entry[namekey][row_index]   
        startfreq = log_entry[' start_frequency '][row_index]
        stopfreq = log_entry[' stop_frequency '][row_index]
    elif type(log_entry) is list:
        # Process by index. Assume it's still a whole row.
        iqdata = log_entry[4]
        iqdata = (iqdata.split("{")[1]).split("}")[0]
        iqdata = [float(x) for x in iqdata.split(",")]

        measurement_type = log_entry[6]
        startfreq = log_entry[1]
        stopfreq = log_entry[2]
    else:
        print("I don't recognize this log format. Please provide a NA log database row as either a dict or list")
        return None
    
    freqs=np.linspace(startfreq,stopfreq,int(len(iqdata)/2))
    if "reflection" in measurement_type:
        print("Attempting to fit a reflection measurement")
        fit_dict = fit_reflection(iqdata,freqs)
        fit_dict["type"] = "Reflection"
        fit_dict["iq_fit_shape"] = fit_dict["fit_shape"]
        fit_dict["fit_shape"] = iq_packed2powers(fit_dict["iq_fit_shape"])
    elif "transmission" in measurement_type:
        print("Attempting to fit a transmission measurement")
        powers = iq_packed2powers(iqdata)
        fit_dict = fit_transmission(powers,freqs)
        fit_dict["type"] = "Transmission"
    elif "widescan" in measurement_type:
        print("Attempting to fit a widescan measurement")
        powers=iq_packed2powers(iqdata)
        data_fraction=0.05 #5 percent seems to work, change as you please
        fit_dict = {}
        fit_dict["peaks"]=find_peaks(powers,data_fraction,startfreq,stopfreq).tolist()
    else:
        print("I don't recognize this measurement type: {}".format(measurement_type))
        return None

    return fit_dict

if __name__=='__main__':
  print("network_analyzer_fits: This module perfoms least-squares fits of network analyzer data for use in calibrations and diagnostics.")
  print("To execute a standalone fit, call this module's fit_na_log(<NA log database entry*>)")
  print("   *Pass the full database entry row as a list")
  print("Alternatively, call the appropriate fit using the raw NA data:")
  print("    ref_fit_dict = fit_reflection(iq_data,frequencies)")
  print("    trans_fit_dict = fit_transmission(powers,frequencies)")
  print("        *powers can be calculated by calling network_analyzer_fits.iq_packed2powers(iq_data)")