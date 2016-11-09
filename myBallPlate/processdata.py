#!/usr/bin/env python

''' Access will always be in control values (maybe value?) '''
import pickle
from matplotlib import use
use('TkAgg')
from matplotlib import rcParams
rcParams['ps.useafm'] = True
rcParams['pdf.use14corefonts'] = True

from matplotlib.pyplot import gca, grid, subplots_adjust,figure, xlabel, ylabel, title, savefig, show, legend, subplot, boxplot, axes, hist, savefig, xlim, ylim, plot, hist2d, axis, close as figclose
from matplotlib.colors import LogNorm
from numpy import median, arange, zeros, searchsorted, genfromtxt, argsort, diff, sqrt, where, cos, sin, fmod, mean, array, pi, isnan, vstack, hstack
from sys import argv
from time import time as clock

from math import sin, cos, sqrt, asin, isnan, isinf, pi


import dpkt
import datetime
import socket
import cStringIO
import string
from re import search
from operator import itemgetter
from sys import exc_info


ykernel = 'butterfly2';yamplitude = 2.0;yfrequency = 1.0/100.00;psikernel = 'butterfly1';psiamplitude = 0*pi/180;psifrequency = 1.0/125.0;xkernel = 'butterfly1';xamplitude = 2.0;xfrequency = 1.0/100.00

#Reference function -- gets reference at a time t
def ref(time,kernel,amplitude,frequency):
    if kernel == 'butterfly1':
        val = amplitude*cos(2*pi*time*frequency)*sin(4*pi*time*frequency);
    elif kernel == 'butterfly2':
        val = amplitude*cos(2*pi*time*frequency)*sin(2*pi*time*frequency);
    elif kernel == 'square':
        if sin(frequency*2*pi*time) < 0:
            val = -amplitude;
        else:
            val = amplitude;
    elif kernel == 'sin':
        val = amplitude*sin(frequency*2*pi*time);
    elif kernel == 'cos':
        val = amplitude*cos(frequency*2*pi*time);
    return val

def process(filename):
    data = genfromtxt(filename, skip_header=1, skip_footer=1,invalid_raise=False)
    sorted_indices = argsort(data[:,5])
    data = data[sorted_indices,:]
    #d0max=searchsorted(data[:,0],[00,7100], side='left')
    #data = data[d0max[0]+1:d0max[1],:]
    #data = array([i for i in data if not isnan(i[1])])
    return data

broker_ip = "128.110.152.120"
host_ip = "192.168.0.6"

def ip_to_str(address):
    """Print out an IP address given a string
        
        Args:
        address: the string representation of a MAC address
        Returns:
        printable IP address
        """
    return socket.inet_ntop(socket.AF_INET, address)

# def isclose(a, b, allowed_error = .001):
# 	return abs(a - b) <= allowed_error

def remove_duplicates(seq):
    final_list = []
    seen = set()
    seen_add = seen.add
    for item in seq:
        time = round(item[0], 2)
        if time not in seen:
            final_list.append(item)
        seen_add(time)

    sorted_indices = argsort([i[0] for i in final_list])
    final_list = [final_list[i] for i in sorted_indices]

    return final_list

def analyzetcp(capturefile, remote='130.127.48.67'):
    ## custom code to recognize data to and from 130.127.48.67
    f = open(capturefile)
    pcap = dpkt.pcap.Reader(f)
    state_list = []
    control_list = []
    times = []
    t0 = None
    
    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)
        if t0 is None: t0 = datetime.datetime.utcfromtimestamp(ts) ;
        
        # IP object includes information such as IP Address
        ip = eth.data;
        if type(ip.data) is dpkt.tcp.TCP:
            #print ts, len(buf), ip.data.data, socket.inet_ntoa(ip.src), socket.inet_ntoa(ip.dst)
            try:
                # This includes TCP header information
                tcp = ip.data;
                
                # if "]" in tcp.data and "value" not in tcp.data and " " in tcp.data:
                if socket.inet_ntoa(ip.src) in remote and "value" in tcp.data and "&t=" in tcp.data:
                    #print tcp.data
                    #print 'Timestamp: ', str(datetime.datetime.utcfromtimestamp(ts)) , 'IP: %s -> %s (len=%d, syn=%d, ack=%d)' % (ip_to_str(ip.src), ip_to_str(ip.dst), ip.len, syn_flag, ack_flag)
                    #print tcp.data
                    time = tcp.data.rsplit("t=")[1].rsplit("&")[0]
                    control_list.append([float(time), datetime.datetime.utcfromtimestamp(ts) - t0])
                elif socket.inet_ntoa(ip.src) in remote and "value" in tcp.data and "&time=" in tcp.data:
                    #print tcp.data
                    #print 'Timestamp: ', str(datetime.datetime.utcfromtimestamp(ts)) , 'IP: %s -> %s (len=%d, syn=%d, ack=%d)' % (ip_to_str(ip.src), ip_to_str(ip.dst), ip.len, syn_flag, ack_flag)
                    #print tcp.data
                    time = tcp.data.rsplit("time=")[1].rsplit("&")[0];
                    control_list.append([float(time), datetime.datetime.utcfromtimestamp(ts) - t0])
                elif socket.inet_ntoa(ip.dst) in remote and len(tcp.data)> 20 and ']' in tcp.data and "value" not in tcp.data :

                    m = search('\[(.+?) (.+?) (.+?) (.+?) (.+?)\](.+?)\[(.+?) (.+?) (.+?) (.+?) (.+?)\]', tcp.data)
                    if m:
                        if len(m.groups()) == 11:
                            time = m.group(5).split()[-1]
                            state_list.append([float(time), datetime.datetime.utcfromtimestamp(ts) - t0])
                            time = m.group(11).split()[-1]
                            state_list.append([float(time), datetime.datetime.utcfromtimestamp(ts) - t0])
                        else:
                            print "should be long", tcp.data
                    else:
                        m = search('\[(.+?) (.+?) (.+?) (.+?) (.+?)\]', tcp.data)
                        if m:
                            time = m.groups()[-1].split()[-1];
                            state_list.append([float(time), datetime.datetime.utcfromtimestamp(ts) - t0])
                        #else:
                        #    print "should be short", tcp.data
                #else:
                #print "don't know", tcp.data, socket.inet_ntoa(ip.dst)
            except :
                print tcp.data, "error!", exc_info(),"\n";
        else: #packet is not a TCP packet
            pass
    '''
    figure(101)
    mydat=array([ (i[1]-control_list[0][1]).total_seconds() for i in control_list])
    latency = mydat- arange(0,round(len(mydat)*.2,2),.2)
    hist(latency - min(latency), 100, log=True);xlim([-.1,.6]);ylim([1,37000]);grid("on",which="both");
    xlabel('Relative latency in control request (s)')
    savefig(capturefile.replace("/","_")[3:-3]+"eps" , format='eps')
    figclose(101)
    '''
    
    state_list = remove_duplicates(state_list)
    control_list = remove_duplicates(control_list)
    state_count, control_count = 0,0
    while state_count < len(state_list) and control_count < len(control_list):
        #print state_list[state_count][0], control_list[control_count][0]
        if state_list[state_count][0] == control_list[control_count][0]:
            delta = state_list[state_count][1] - control_list[control_count][1]
            times.append([delta,state_list[state_count][0],state_list[state_count][1], control_list[control_count][1]])
            state_count+=1
            control_count+=1
        elif state_list[state_count][0] > control_list[control_count][0]:
            times.append([float("inf"),state_list[state_count][0],state_list[state_count][1], control_list[control_count][1]])
            control_count+=1
        elif state_list[state_count][0] < control_list[control_count][0]:
            times.append([float("inf"),state_list[state_count][0],state_list[state_count][1], control_list[control_count][1]])
            state_count+=1
    f.close()
    return times;

def errors(data):
    number=16
    q=array([item  for item in data[0:2000,:] if not isnan(item[1])]);xnew=arange(q[0,0]+.01,q[-1,0],.01);ius=interp1d(q[:,0],q[:,2], kind='linear', axis=-1, copy=True, bounds_error=True);ynew1=ius(xnew);ius=interp1d(q[:,0],q[:,7], kind='linear', axis=-1, copy=True, bounds_error=True); ynew2=ius(xnew);xcorr = correlate(ynew1,ynew2);datadt=arange(1-xnew.shape[0],xnew.shape[0])[xcorr.argmax()];
    
    e_data0 = array([[item[0]-datadt*.01,item[1] - ref(item[0]-datadt*.01,xkernel ,xamplitude ,xfrequency) ,item[2] - ref(item[0]-datadt*.01,ykernel ,yamplitude ,yfrequency)] for item in data if not isnan(item[1])]);
    #e_data1 = array([[item[14]-datadt*.01,item[1] - ref(item[14]-datadt*.01,xkernel ,xamplitude ,xfrequency) ,item[2] - ref(item[14]-datadt*.01,ykernel ,yamplitude ,yfrequency)] for item in data if not isnan(item[1])]);
    errors = [None]*number;
    counts = [None]*number;
    
    for count in range(1,number+1):
        #get the range of indices that are relevant for this loop
        d0max=searchsorted(e_data0[:,0],[.1+100*count,.1+100*count+100], side='left');
        '''since the controller can get delayed, it's possible that the time is off by a cycle.. and instead of the 0 index, the 14 index has the correct time.
            To work around this issue we take the minimum error of both time calculations.
            '''
        #errors[count-1] = sum(abs(data[d0max[0]:d0max[1],1]))/diff(d0max)+sum(abs(data[d0max[0]:d0max[1],2]))/diff(d0max); #old value not correct for some cases
        errors[count-1] = min(sum(abs(e_data0[d0max[0]:d0max[1],1]))/diff(d0max)+sum(abs(e_data0[d0max[0]:d0max[1],2]))/diff(d0max),sum(abs(e_data1[d0max[0]:d0max[1],1]))/diff(d0max)+sum(abs(e_data1[d0max[0]:d0max[1],2]))/diff(d0max))
        counts[count-1] = d0max[1]-d0max[0];
    
    e_data=errors;
    e_datac=counts;
    return e_data, e_datac



if __name__ == "__main__":
    path = argv[1]
    controller1_l5=process(path+"/mqtt_bar_n2oEast_new.txt");
    controller1_l4=analyzetcp(path+'/Controller.pcap','10.0.0.3');


    hist([i[0].total_seconds() for i in controller1_l4 if type(i[0]) is not float],100);
    grid("on",which="both");#xlim([0,.8]);ylim([0,1e5])
    title("Histogram of the Transport Layer RTT n="+str(len(controller1_l4)))

    figure();plot(controller1_l5[:,0],controller1_l5[:,1]);plot(controller1_l5[:,0],controller1_l5[:,6]);title("x-axis");legend(["actual","target"])
    figure();plot(controller1_l5[:,0],controller1_l5[:,2]);plot(controller1_l5[:,0],controller1_l5[:,7]);title("y-axis");legend(["actual","target"])
    show()



