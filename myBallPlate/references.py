from math import sin, cos, sqrt, asin, isnan, isinf, pi

#Reference function -- gets reference at a time t
def ref(time,kernel,amplitude,frequency):
    #frequency = 1*1.0/100.0
    if kernel == 'butterfly1':
        val = amplitude*cos(2*pi*time*frequency)*sin(4*pi*time*frequency)
    elif kernel == 'butterfly2':
        val = amplitude*cos(2*pi*time*frequency)*sin(2*pi*time*frequency)
    elif kernel == 'square':
        if sin(frequency*2*pi*time) < 0:
            val = -amplitude 
        else:
            val = amplitude 
    elif kernel == 'sin':
        val = amplitude*sin(frequency*2*pi*time)
    elif kernel == 'cos':
        val = amplitude*cos(frequency*2*pi*time)

    return val


