#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 21:17:10 2020

@author: aroman
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  7 16:33:33 2020

@author: aroman
"""
import numpy as np
import theano
import theano.tensor as tt
theano.config.gcc.cxxflags = "-Wno-c++11-narrowing"
import pymc3 as pm
import pickle as pickle
import matplotlib.pyplot as plt
import sys
import corner
sys.path.insert(1,'../../')
import matplotlib.gridspec as gridspec

path_results = '../../../results/'

g = 9.8
rho = 2700
#chamber and elasticity
#Elastic properties crust
poisson = 0.25
lame = 3e+9
lamesar = 1e+9 
cs = -9. /(4 * 3.14) * (1 - poisson) / lame
#Position of the chamber
#Piston geometrical parameters
Rp = 7e+2
S = 3.14 * Rp**2
#Conduit Properties
mu = 1e+2
ls = 4e+4
ld = 2.5e+3
data = pickle.load(open('data2ch.pickle','rb'))
dtslip,tiltsty,tiltstx,tiltsly,tiltslx,gps,stack,tstack,xsh,ysh,dsh,xshErr,yshErr,dshErr,strsrc,strsrcErr = data
strsrc = strsrc * lame / lamesar
strsrcErr = strsrcErr * lame / lamesar
tilt_std = 1e-5
dt_std = 3600
gps_std = 1
ref_point = np.array([-155.274,19.395])  # Ref point is alway CRIM
x = -1774.
y  = 2867.
Nmin = 2
Nmax = 70
n = np.arange(1,len(tiltsty)+ 1 )
#Setup inversion
pi = 3.14
Niter = 300000
#conds_mod = 3.5
path_results = '../../../results/'
with pm.Model() as model:
    gpsconst = pm.Uniform('gpsconst',lower = -15,upper = 15)
    A_mod = pm.Uniform('A_mod',lower = 0,upper = 1000)
    B_mod = pm.Uniform('B_mod',lower = 0, upper = 1000)
    E_mod = pm.Uniform('E_mod',lower = 0,upper = 1000)
    Vs_exp = pm.Uniform('Vs_exp',lower = 8,upper = 11)
    Vs_mod = pm.Deterministic('Vs_mod',10**Vs_exp)
    ks_exp = pm.Uniform('ks_exp',lower = 7, upper = 10)
    ks_mod = pm.Deterministic('ks_mod',10**ks_exp)
    R1 = pm.Deterministic('R1',rho * g * Vs_mod /(ks_mod * S)  )
    ratio = pm.Uniform('ratio',lower = 30 * 2 * R1 / (1 + R1), upper = 120 * 2 * R1 / (1 + R1))
    pspd_mod = pm.Uniform('pspd_mod',lower=1e+5,upper=1e+7)
    ptps_mod = pm.Deterministic('ptps_mod',ratio * pspd_mod)

    deltap_mod = pm.Uniform('deltap',lower = 1e+5,upper = ptps_mod )
    strsrc_mod = pm.Normal('strsrc_Mod',mu = strsrc, sigma = strsrcErr)
    Vd_mod = pm.Deterministic('Vd_mod',strsrc_mod / deltap_mod)

    #kd_exp = pm.Uniform('kd_exp',lower = 8, upper = 11)

    
    conds_mod = pm.Uniform('conds_mod',lower=1,upper=10)
    condd_mod = pm.Uniform('condd_mod',lower=1,upper=30)
    dsh_mod = pm.Normal('dsh_mod',mu = dsh, sigma = dshErr)
    xsh_mod = pm.Normal('xsh_mod',mu = xsh, sigma = xshErr)
    ysh_mod = pm.Normal('ysh_mod',mu = ysh, sigma = yshErr)
    coeffx = cs * dsh_mod * (x -  xsh_mod) / (dsh_mod**2 + (x -  xsh_mod)**2 + (y -  ysh_mod)**2 )**(5./2) * Vs_mod
    coeffy = cs * dsh_mod * (y -  ysh_mod) / (dsh_mod**2 + (x -  xsh_mod)**2 + (y -  ysh_mod)**2 )**(5./2) * Vs_mod
    tau2 = 8 * mu *ld * Vs_mod/ (3.14 * condd_mod**4 * ks_mod)    #Model set-up
    x_mod =gpsconst+ 4 * R1 / (rho * g) * pspd_mod / (1 + R1) * n
    
    pslip_mod = -rho * g * x_mod
    pstick_mod = pslip_mod + 4 * pspd_mod/ (1 + R1)

    tslx_mod = coeffx * pslip_mod
    tsly_mod = coeffy * pslip_mod
    tstx_mod = coeffx * pstick_mod
    tsty_mod = coeffy * pstick_mod    

    T1 = (conds_mod / condd_mod )**4 * ld /ls
    phi = 1 * Vs_mod / Vd_mod
    #phi = ratio  * Vs_mod / kd_mod
    stack_mod  = A_mod * tt.exp(tstack/tau2*(-T1/2 - phi/2 + tt.sqrt(4*phi + (-T1 + phi - 1)**2)/2 - 1/2)) + B_mod * tt.exp(tstack/tau2*(-T1/2 - phi/2 - tt.sqrt(4*phi + (-T1 + phi - 1)**2)/2 - 1/2))  - E_mod
    #Posterio
    tslx_obs = pm.Normal('tslx_obs', mu=tslx_mod, sigma = tilt_std, observed=tiltslx)
    tsly_obs = pm.Normal('tsly_obs', mu=tsly_mod, sigma = tilt_std, observed=tiltsly)
    tstx_obs = pm.Normal('tstx_obs', mu=tstx_mod, sigma = tilt_std, observed=tiltstx)
    tsty_obs = pm.Normal('tsty_obs', mu=tsty_mod, sigma = tilt_std, observed=tiltsty)
    
    
    
    x_obs = pm.Normal('x_obs', mu = x_mod, sigma = gps_std, observed=gps)
    stack_obs = pm.Normal('stack_obs', mu = stack_mod, sigma = tilt_std*1e+6, observed=stack)
    trace2 = pm.load_trace(path_results + 'trace300000_strsrc_UF')
panda_trace = pm.backends.tracetab.trace_to_dataframe(trace2)
panda_trace['Vs_mod'] = np.log10(panda_trace['Vs_mod']) 
panda_trace['ks_mod'] = np.log10(panda_trace['ks_mod']) 
panda_trace['Vd_mod'] = np.log10(panda_trace['Vd_mod']) 
panda_trace['pspd_mod'] = panda_trace['pspd_mod'] / 1e+6  
filename = 'res300000_strsrc_UF.pickle'
results =pickle.load(open(path_results + filename,'rb'))

R1 = rho * g * results['MAP']['Vs_mod'] /(results['MAP']['ks_mod'] * S)    
xMAP = results['MAP']['gpsconst']+ 4 * R1 / (rho * g) * results['MAP']['pspd_mod'] / (1 + R1) * n
pslipMAP =  -rho * g * xMAP
pstickMAP = pslipMAP + 4 * results['MAP']['pspd_mod']/ (1 + R1)
T1 = (results['MAP']['conds_mod']/ results['MAP']['condd_mod'] )**4 * ld /ls
phi = 1 * results['MAP']['Vs_mod'] / results['MAP']['Vd_mod']
coeffx = cs * results['MAP']['dsh_mod'] * (x -  results['MAP']['xsh_mod']) / (results['MAP']['dsh_mod']**2 + (x -  results['MAP']['xsh_mod'])**2 + (y -  results['MAP']['ysh_mod'])**2 )**(5./2) * results['MAP']['Vs_mod']
coeffy = cs * results['MAP']['dsh_mod'] * (y -  results['MAP']['ysh_mod']) / (results['MAP']['dsh_mod']**2 + (x -  results['MAP']['xsh_mod'])**2 + (y -  results['MAP']['ysh_mod'])**2 )**(5./2) * results['MAP']['Vs_mod']
tau2 = 8 * mu *ld * results['MAP']['Vs_mod']/ (3.14 * results['MAP']['condd_mod']**4 * results['MAP']['ks_mod'])
stackMAP  = results['MAP']['A_mod'] * np.exp(tstack/tau2*(-T1/2 - phi/2 + np.sqrt(4*phi + (-T1 + phi - 1)**2)/2 - 1/2)) + results['MAP']['B_mod'] * np.exp(tstack/tau2*(-T1/2 - phi/2 - np.sqrt(4*phi + (-T1 + phi - 1)**2)/2 - 1/2))  - results['MAP']['E_mod']
tslxMAP =coeffx * pslipMAP
tstxMAP =coeffx * pstickMAP
tslyMAP =coeffy * pslipMAP
tstyMAP =coeffy * pstickMAP
ppc = pm.sample_posterior_predictive(trace2, samples=500, model=model)

xmed = np.median(ppc['x_obs'],axis = 0)
xstd = np.std(ppc['x_obs'],axis = 0)

tslxmed = np.median(ppc['tslx_obs'],axis = 0)
tslymed = np.median(ppc['tsly_obs'],axis = 0)
tslxstd = np.std(ppc['tslx_obs'],axis = 0)
tslystd = np.std(ppc['tsly_obs'],axis = 0)

tstxmed = np.median(ppc['tstx_obs'],axis = 0)
tstymed = np.median(ppc['tsty_obs'],axis = 0)
tstxstd = np.std(ppc['tstx_obs'],axis = 0)
tstystd = np.std(ppc['tsty_obs'],axis = 0)
ticks = np.arange(1,20)
ticks = ticks[::2]
fig = plt.figure(figsize=(5, 8))
gs = gridspec.GridSpec(nrows=3, ncols=10, height_ratios=[1, 1, 1])
ax0 = fig.add_subplot(gs[0, 1:-1])
ax0.plot(n,gps,'bo')
ax0.plot(n,xMAP,'mo')
ax0.errorbar(n,xmed,xstd,fmt='none')
ax0.set_ylabel('CALS [m]',fontsize= 12)
ax0.set_xticks(ticks)
ax0.legend(['Data','MAP'],fontsize= 10)

ax1 = fig.add_subplot(gs[1, 1:-1])

ax1.plot(n,tiltslx*1e+6,'bo')
ax1.plot(n,tslxMAP*1e+6,'mo')
ax1.errorbar(n,tslxmed*1e+6,tslxstd*1e+6,fmt='none',ecolor = 'k' )

ax1.plot(n,tiltstx*1e+6,'bo')
ax1.plot(n,tstxMAP*1e+6,'mo')
ax1.errorbar(n,tstxmed*1e+6,tstxstd*1e+6,fmt='none',ecolor = 'k')
ax1.set_ylabel('UWD EW [$\mu$rad]',fontsize= 12)
ax1.set_xticks(ticks)

ax2 = fig.add_subplot(gs[2, 1:-1])
ax2.plot(n,tiltsly*1e+6,'bo')
ax2.plot(n,tslyMAP*1e+6,'mo')
ax2.errorbar(n,tslymed*1e+6,tslystd*1e+6,fmt='none',ecolor = 'k')

ax2.plot(n,tiltsty*1e+6,'bo')
ax2.plot(n,tstyMAP*1e+6,'mo')
ax2.errorbar(n,tstymed*1e+6,tstystd*1e+6,fmt='none',ecolor = 'k')

ax2.set_ylabel('UWD NS [$\mu$rad]',fontsize= 12)
ax2.set_xlabel('Collapse number',fontsize= 12)
ax2.set_xticks(ticks)

plt.tight_layout()
fig.align_ylabels()

plt.savefig('MAPcollapses_strsrc_UF.pdf')

stackmed = np.median(ppc['stack_obs'],axis = 0)
stackstd = np.std(ppc['stack_obs'],axis = 0)
tstack = tstack/(3600)

plt.figure()
plt.plot(tstack,stack+180,'b')
plt.plot(tstack,stackMAP+180,'m')
plt.fill_between(tstack,stackmed-stackstd+180,stackmed+stackstd+180,alpha = 0.5)
ax = plt.gca()
ax.set_xlabel('Time [Hours]',fontsize= 12)
ax.set_ylabel('UWD NS [$\mu rad$]',fontsize = 12)
ax.set_xlim([0,24])
plt.tight_layout()
plt.savefig('MAPstack_strsrc_UF.pdf')

plt.figure()
corner.corner( panda_trace[['xsh_mod','ysh_mod','dsh_mod','pspd_mod','condd_mod','conds_mod','ks_mod','Vs_mod','Vd_mod','ptps_mod']],color = 'black',
              truths =[results['MAP']['xsh_mod'],results['MAP']['ysh_mod'],results['MAP']['dsh_mod'],results['MAP']['pspd_mod']/1e+6,results['MAP']['condd_mod'],results['MAP']['conds_mod'],np.log10(results['MAP']['ks_mod']),np.log10(results['MAP']['Vs_mod']),np.log10(results['MAP']['Vd_mod']),results['MAP']['ptps_mod']])
