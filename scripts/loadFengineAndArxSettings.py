# Script to configure F engines and ARX boards
# USAGE:  $python loadFengineAndArxSettings.py <eqFile.mat>

# 20221117 Initial version of F engine setting.
# 20230105 Add 7th coef set for fiber-connected signals. 
# 20230203 Include ARX setting.
# 20230211 Include delay setting.
# 20230211 Use etcd interface for F engine settings.

import sys
import scipy.io as mat
import time
import numpy as np

# Constants
DELAY_OFFSET = 10 # minimum delay
ADC_CLOCK = 196000000    # sampling clock frequency, Hz
ETCDHOST = 'etcdv3service.sas.pvt'


# Read configuration data file
config = mat.loadmat(sys.argv[1],squeeze_me=True)
print('Read data file',sys.argv[1])
print('Data file internal time: ',time.asctime(time.gmtime(config['time'])))


#=====================================
# LOAD F ENGINE EQUALIZATION FUNCTIONS
#-------------------------------------

#import myfengines as f
from mnc.fengFunctions import dsig2feng
from lwa_f import snap2_feng_etcd_client
ec = snap2_feng_etcd_client.Snap2FengineEtcdControl(ETCDHOST)

print('Connected to ETCD host %s' % ETCDHOST)
cfgkeys = config.keys()

# Set FFT shift to maximum for all boards      
for i in range(11):
    #f.f[i].pfb.set_fft_shift(0x1FFF)  # Request shift at all FFT stages
    ec.send_command(i+1,'pfb','set_fft_shift',kwargs={'shift':0x1FFF})
    print('snap%02d:'%(i+1)," fft shift set")

coef = config['coef']   # must include this key
dsigDone = []

k = 'eq0'   # coax length = ref+-50m
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[0])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(int(loc[1])),'coeffs':coef[0].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq1'   # coax: shortest
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[1])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[1].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq2'   # coax: next 40m
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[2])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[2].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq3'   # coax: next 40m
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[3])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[3].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq4'   # coax: next 40m
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[4])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[4].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq5'   # coax: longest
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[5])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[5].tolist()})
        dsigDone.append(i)
    print(dsig)

k = 'eq6'   # fiber
if k in cfgkeys:
    dsig = config[k]
    for i in dsig:
        loc = dsig2feng(i)
        #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[6])
        ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[6].tolist()})
        dsigDone.append(i)
    print(dsig)

# All others (if any): set same as reference
for i in range(704):  # all others
    if i in dsigDone: continue
    loc = dsig2feng(i)
    #f.f[loc[0]-1].eq.set_coeffs(int(loc[1]),coef[0])
    ec.send_command(loc[0],'eq','set_coeffs',kwargs={'stream':int(loc[1]),'coeffs':coef[0].tolist()})
    
#=============================
# LOAD F ENGINE DELAY SETTINGS
#-----------------------------

if 'delay_dsig' in config.keys():

    delays_ns = np.array(config['delay_dsig']) # delays in order of digital sig No., nanoseconds
    
    max_delay_ns = delays_ns.max()
    delays_clocks = np.round(delays_ns*1e-9 * ADC_CLOCK).astype(int)
    max_delay_clocks = delays_clocks.max()

    relative_delays_clocks = max_delay_clocks - delays_clocks
    max_relative_delay_clocks = delays_clocks.max()

    delays_to_apply_clocks = relative_delays_clocks + DELAY_OFFSET
    print(delays_to_apply_clocks)
    
    print('Maximum delay: %f ns' % max_delay_ns)
    print('Maximum delay: %d ADC clocks' % max_delay_clocks)
    print('Maximum relative delay: %d ADC clocks' % max_relative_delay_clocks)
    print('Maximum delay to be applied: %d ADC clocks' % delays_to_apply_clocks.max())
    print('Minimum delay to be applied: %d ADC clocks' % delays_to_apply_clocks.min())

    for dsig in range(len(delays_ns)):
        sig = dsig2feng(dsig)
        snap_id = sig[0]
        input_id = sig[1]
        print(dsig,snap_id,input_id,delays_to_apply_clocks[dsig])
        ec.send_command(snap_id, 'delay', 'set_delay', kwargs={'stream':input_id, 'delay':int(delays_to_apply_clocks[dsig])})
        #f.f[snap_id-1].delay.set_delay(input_id,int(delays_to_apply_clocks[dsig]))

    
#======================
# NOW LOAD ARX SETTINGS
#----------------------

import mnc.myarx as a

adrs = config['adrs']
settings = config['settings']
print('ARX: ',adrs)

for i in range(len(adrs)):
    codes = ''
    for j in range(16):
        s = settings[i][j]
        codes += a.chanCode(s[0],s[1],s[2],s[3])
    try:
        a.raw(adrs[i],'SETA'+codes)
        print('Loaded: ',adrs[i],codes)
        print(settings[i])
    except:
        continue

