import math
import numpy as np
import cmath
from scipy.optimize import least_squares
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy import stats


__all__ = []

def transmission_fit_options(powers,frequencies,fit_type):
    if fit_type == "cavity":
        return fit_transmission_cavity(powers,frequencies)
    elif fit_type == "jpa":
        return fit_transmission_jpa(powers,frequencies)
    
def reflection_fit_options(powers,frequencies,fit_type):
    if fit_type == "cavity":
        return fit_reflection_cavity(powers,frequencies)
    elif fit_type == "jpa":
        return fit_reflection_jpa(powers,frequencies)


def transmission_power_shape_cavity(f, norm, f0, Q):
    """returns the expected power from a transmission measurement at frequency f with parameters
        f0 - resonant frequency
        Q - resonant quality
        norm - normalization of the resonance
        noise - estimate of the noise background"""
    delta=Q*(f-f0)/f0
    return norm*(1/(1+4*delta*delta))

def transmission_power_shape_jpa(f, norm, f0, Q, f_jpa, Q_jpa):
    """returns the expected power from a transmission measurement at frequency f with parameters
        f0 - resonant frequency
        Q - resonant quality
        norm - normalization of the resonance
        noise - estimate of the noise background"""
    delta=Q*(f-f0)/f0
    delta_i = np.flip(delta)
    delta_jpa=Q_jpa*(f-f_jpa)/f_jpa
    return norm*np.max(np.array([1/(1+4*delta**2),1/(1+4*delta_i**2)]),axis=0)*(1/(1+4*delta_jpa*delta_jpa))

def reflection_power_shape_cavity(f, norm, f0, Q):
    """returns the expected power from a transmission measurement at frequency f with parameters
        f0 - resonant frequency
        Q - resonant quality
        norm - normalization of the resonance
        noise - estimate of the noise background"""
    delta=Q*(f-f0)/f0
    return norm*(1-(1/(1+4*delta*delta)))

def reflection_power_shape_jpa(f, norm, f0, Q, f_jpa, Q_jpa):
    """returns the expected power from a transmission measurement at frequency f with parameters
        f0 - resonant frequency
        Q - resonant quality
        norm - normalization of the resonance
        noise - estimate of the noise background"""
    delta=Q*(f-f0)/f0
    delta_i = np.flip(delta)
    delta_jpa=Q_jpa*(f-f_jpa)/f_jpa
    return norm*(1-np.max(np.array([1/(1+4*delta**2),1/(1+4*delta_i**2)]),axis=0))*(1/(1+4*delta_jpa*delta_jpa))


def fit_transmission_jpa(powers,frequencies):
    """
        Performs a least-squares fit on a transmission measurement, an array of powers and frequencies
    """
    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    f0_guess=frequencies[int(math.floor(3*len(frequencies)/4))]

    norm_guess=max(powers)
    f_jpa_guess=(frequencies[0]+frequencies[-1])/2
    Q_min=1000
    Q_max=100000
    Q_guess=20000
    Q_jpa_min = 100
    Q_jpa_max = 20000
    Q_jpa_guess = 5000
    p0=[norm_guess,f0_guess,Q_guess,f_jpa_guess,Q_jpa_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=4
        norm=x[0]
        f0=x[1]
        Q=x[2]
        f_jpa=x[3]
        Q_jpa=x[4]
        resid=np.zeros(nfreq+npriors)
        if f0<frequencies[0]:
            resid[nfreq]=(f0-frequencies[0])/f0_guess
            f0=frequencies[0]
        if f0>frequencies[-1]:
            resid[nfreq]=(frequencies[-1]-f0)/f0_guess
            f0=frequencies[-1]
        if Q<Q_min:
            resid[nfreq+1]=10*nfreq*(Q-Q_min)/Q_min
            Q=Q_min
        if Q>Q_max:
            resid[nfreq+1]=10*nfreq*(Q_max-Q)/Q_min
            Q=Q_max
        if f_jpa<frequencies[0]:
            resid[nfreq+2]=(f_jpa-frequencies[0])/f_jpa_guess
            f0=frequencies[0]
        if f_jpa>frequencies[-1]:
            resid[nfreq+2]=(frequencies[-1]-f_jpa)/f_jpa_guess
            f0=frequencies[-1]
        if Q_jpa>Q_jpa_max:
            resid[nfreq+3]=10*nfreq*(Q_jpa-Q_jpa_min)/Q_jpa_min
            Q_jpa = Q_jpa_max
        if Q_jpa < Q_jpa_min:
            resid[nfreq+3]=10*nfreq*(Q_jpa_max-Q_jpa)/Q_jpa_max
            Q_jpa = Q_jpa_min
        resid[:nfreq]=transmission_power_shape_jpa(frequencies,norm,f0,Q,f_jpa,Q_jpa) - powers
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape = transmission_power_shape_jpa(frequencies,res.x[0],res.x[1],res.x[2],res.x[3],res.x[4])
    #return norm,f0,Q,norm_jpa,f_jpa,Q_jpa, chi square, fit shape
    return [res.x[0],res.x[1],res.x[2],res.x[3],res.x[4],chisq,fit_shape]

def fit_transmission_cavity_old(powers,frequencies):
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

    f0_guess=frequencies[int(math.floor(len(frequencies)/2))]
    f_band=frequencies[-1]-frequencies[0]
    norm_guess=max(powers)
    Q_min=f0_guess/f_band
    Q_max=20*Q_min
    Q_guess=0.5*(Q_max+Q_min)
    p0=[norm_guess,f0_guess,Q_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=2
        norm=x[0]
        f0=x[1]
        Q=x[2]
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
        for i in range(nfreq):
            yp=transmission_power_shape_cavity(frequencies[i],norm,f0,Q)
            resid[i]=(yp-powers[i])
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape=[ transmission_power_shape_cavity(f,res.x[0],res.x[1],res.x[2]) for f in frequencies ]
    #return norm,f0,Q,noise, chi square, fit shape
    return [res.x[0],res.x[1],res.x[2],chisq,fit_shape]

def fit_transmission_cavity(powers,frequencies):
    """
        Performs a least-squares fit on a transmission measurement, an array of powers and frequencies
    """
    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit transmission, need 16, got {}".format(len(powers)))

    f0_guess=frequencies[int(math.floor(3*len(frequencies)/4))]

    norm_guess=max(powers)
    Q_min=1000
    Q_max=100000
    Q_guess=20000

    p0=[norm_guess,f0_guess,Q_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=2
        norm=x[0]
        f0=x[1]
        Q=x[2]
        resid=np.zeros(nfreq+npriors)
        if f0<frequencies[0]:
            resid[nfreq]=(f0-frequencies[0])/f0_guess
            f0=frequencies[0]
        if f0>frequencies[-1]:
            resid[nfreq]=(frequencies[-1]-f0)/f0_guess
            f0=frequencies[-1]
        if Q<Q_min:
            resid[nfreq+1]=10*nfreq*(Q-Q_min)/Q_min
            Q=Q_min
        if Q>Q_max:
            resid[nfreq+1]=10*nfreq*(Q_max-Q)/Q_min
            Q=Q_max
        resid[:nfreq]=transmission_power_shape_jpa(frequencies,norm,f0,Q) - powers
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape = transmission_power_shape_jpa(frequencies,res.x[0],res.x[1],res.x[2])
    #return norm,f0,Q,norm_jpa,f_jpa,Q_jpa, chi square, fit shape
    return [res.x[0],res.x[1],res.x[2],chisq,fit_shape]

def fit_reflection_cavity(powers,frequencies):
    """
        Performs a least-squares fit on a reflection measurement, an array of powers and frequencies
    """
    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit reflection, need 16, got {}".format(len(powers)))

    f0_guess=frequencies[int(math.floor(3*len(frequencies)/4))]

    norm_guess=max(powers)
    Q_min=1000
    Q_max=100000
    Q_guess=20000

    p0=[norm_guess,f0_guess,Q_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=2
        norm=x[0]
        f0=x[1]
        Q=x[2]
        resid=np.zeros(nfreq+npriors)
        if f0<frequencies[0]:
            resid[nfreq]=(f0-frequencies[0])/f0_guess
            f0=frequencies[0]
        if f0>frequencies[-1]:
            resid[nfreq]=(frequencies[-1]-f0)/f0_guess
            f0=frequencies[-1]
        if Q<Q_min:
            resid[nfreq+1]=10*nfreq*(Q-Q_min)/Q_min
            Q=Q_min
        if Q>Q_max:
            resid[nfreq+1]=10*nfreq*(Q_max-Q)/Q_min
            Q=Q_max
        resid[:nfreq]=reflection_power_shape_cavity(frequencies,norm,f0,Q) - powers
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape = reflection_power_shape_cavity(frequencies,res.x[0],res.x[1],res.x[2])
    #return norm,f0,Q,norm_jpa,f_jpa,Q_jpa, chi square, fit shape
    return [res.x[0],res.x[1],res.x[2],chisq,fit_shape]

def fit_reflection_jpa(powers,frequencies):
    """
        Performs a least-squares fit on a reflection measurement, an array of powers and frequencies
    """
    if len(frequencies)!=len(powers):
        raise ValueError("point count not right nfreqs {} npows {}".format(len(frequencies),len(powers)))
    if len(frequencies)<16:
        raise ValueError("not enough points to fit reflection, need 16, got {}".format(len(powers)))

    f0_guess=frequencies[int(math.floor(3*len(frequencies)/4))]

    norm_guess=max(powers)
    f_jpa_guess=(frequencies[0]+frequencies[-1])/2
    Q_min=1000
    Q_max=100000
    Q_guess=20000
    Q_jpa_min = 100
    Q_jpa_max = 20000
    Q_jpa_guess = 5000
    p0=[norm_guess,f0_guess,Q_guess,f_jpa_guess,Q_jpa_guess]
    def fit_fcn(x):
        #calculate the residuals of the fit as an array
        nfreq=len(frequencies)
        npriors=4
        norm=x[0]
        f0=x[1]
        Q=x[2]
        f_jpa=x[3]
        Q_jpa=x[4]
        resid=np.zeros(nfreq+npriors)
        if f0<frequencies[0]:
            resid[nfreq]=(f0-frequencies[0])/f0_guess
            f0=frequencies[0]
        if f0>frequencies[-1]:
            resid[nfreq]=(frequencies[-1]-f0)/f0_guess
            f0=frequencies[-1]
        if Q<Q_min:
            resid[nfreq+1]=10*nfreq*(Q-Q_min)/Q_min
            Q=Q_min
        if Q>Q_max:
            resid[nfreq+1]=10*nfreq*(Q_max-Q)/Q_min
            Q=Q_max
        if f_jpa<frequencies[0]:
            resid[nfreq+2]=(f_jpa-frequencies[0])/f_jpa_guess
            f0=frequencies[0]
        if f_jpa>frequencies[-1]:
            resid[nfreq+2]=(frequencies[-1]-f_jpa)/f_jpa_guess
            f0=frequencies[-1]
        if Q_jpa>Q_jpa_max:
            resid[nfreq+3]=10*nfreq*(Q_jpa-Q_jpa_min)/Q_jpa_min
            Q_jpa = Q_jpa_max
        if Q_jpa < Q_jpa_min:
            resid[nfreq+3]=10*nfreq*(Q_jpa_max-Q_jpa)/Q_jpa_max
            Q_jpa = Q_jpa_min
        resid[:nfreq]=reflection_power_shape_jpa(frequencies,norm,f0,Q,f_jpa,Q_jpa) - powers
        return resid
    #actual fit done here
    res=least_squares(fit_fcn,p0,xtol=1e-12) #things like df/f are super small, so set xtol extra low
    chisq=res.cost/len(powers)
    #contsruct the fit shape
    fit_shape = reflection_power_shape_jpa(frequencies,res.x[0],res.x[1],res.x[2],res.x[3],res.x[4])
    #return norm,f0,Q,norm_jpa,f_jpa,Q_jpa, chi square, fit shape
    return [res.x[0],res.x[1],res.x[2],res.x[3],res.x[4],chisq,fit_shape]