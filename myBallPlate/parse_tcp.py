#!/usr/bin/env python

''' Access will always be in control values (maybe value?) '''

import dpkt
import datetime
import socket
import cStringIO
import string
import re
from operator import itemgetter

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

	return final_list

f = open('capture.cap')
pcap = dpkt.pcap.Reader(f)

state_list = []
control_list = []
times = []

for ts, buf in pcap:
	eth = dpkt.ethernet.Ethernet(buf)

	# IP object includes information such as IP Address
	ip = eth.data

	# This includes TCP header information
	tcp = ip.data

	# Get SYN and ACK flags
	syn_flag = ( tcp.flags & 0x02 ) != 0
	ack_flag = ( tcp.flags & 0x10 ) != 0


	# if "]" in tcp.data and "value" not in tcp.data and " " in tcp.data:

	# This should be when the controller consumes messages from the broker
	# Must add the plant_state part because some messages have '[' and ']' in their weird topic data
	if re.search(r'\[.+?\]', tcp.data) and ip_to_str(ip.src) == host_ip and "plant_state" in tcp.data:
		#print 'Timestamp: ', str(datetime.datetime.utcfromtimestamp(ts)) , 'IP: %s -> %s (len=%d, syn=%d, ack=%d)' % (ip_to_str(ip.src), ip_to_str(ip.dst), ip.len, syn_flag, ack_flag)

		#print tcp.data
		all_data = re.findall(r'\[.+?\]', tcp.data)

		#print all_data

		for string in all_data:
			time = string[string.rfind(" ") + 1 : len(string) - 1]

			if len(string) >= len("[0.8502 0.02 -0.971 -0.971 .8006]") and time:
				state_list.append([float(time), datetime.datetime.utcfromtimestamp(ts)])

	# This should be messages published from host side
	elif "value" in tcp.data  and ip_to_str(ip.src) == broker_ip:
		#print 'Timestamp: ', str(datetime.datetime.utcfromtimestamp(ts)) , 'IP: %s -> %s (len=%d, syn=%d, ack=%d)' % (ip_to_str(ip.src), ip_to_str(ip.dst), ip.len, syn_flag, ack_flag)
		#print tcp.data
		#time = tcp.data.rsplit("time=")[1].rsplit("&")[0]
		#print tcp.data.rsplit("time=")[1:]
		for string in tcp.data.rsplit("time=")[1:]:	
			time = string[0 : string.rfind("&access")]
			control_list.append([float(time), datetime.datetime.utcfromtimestamp(ts)])

# We should not sort the lists based on their datetime
state_list = sorted (state_list, key=itemgetter(0))
control_list = sorted (control_list, key=itemgetter(0))

# For some reason that is probably obvoius but I won't dig for now
# The state_list needs to be indexed by one more then the control at all times
#state_list.pop(0)
#control_list.pop(0)

state_list = remove_duplicates(state_list)
control_list = remove_duplicates(control_list)

for state, control in zip (state_list, control_list):	

	#print "State is " + str(state[0])
	#print "Control is " + str(control[0])
	if state[0] == control[0]:
		delta = state[1] - control[1]
		times.append(delta)
	else:
		print "These times were not equal:"
		print "Plant state time = " + str(state[0])
		print "Plant timestamp = " + str(state[1])
		print "Controller time = " + str(control[0])
		print "Controller timestamp = " + str(control[1])
		print

total = 0
counter = 0

for time in times:
	total += time.total_seconds()
	counter += 1
	print "Difference in time = " + str(time)

print "The average time was %f" % (total / counter)

f.close()