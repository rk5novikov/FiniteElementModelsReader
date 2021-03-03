'''
Module with math functions for calculation
of stress tensor derivatives
'''


import math


VM = (lambda s: (math.sqrt(2)/2) * math.sqrt((s[0]-s[1])**2 + (s[0]-s[2])**2 + (s[1]-s[2])**2 + 6*(s[3]**2 + s[4]**2 + s[5]**2)))
VM_signe = (lambda s: (math.sqrt(2)/2) * math.sqrt((s[0]-s[1])**2 + (s[0]-s[2])**2 + (s[1]-s[2])**2 + 6*(s[3]**2 + s[4]**2 + s[5]**2)) * math.copysign(1.0, s[0]+s[1]+s[2]))
Magnitude = (lambda u: math.sqrt(sum([i**2 for i in u])))


def check_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def sci_float(f, prec=4, exp_digits=3):
    s = "%.*e"%(prec, f)
    mantissa, exp = s.split('e')
    return "%sE%+0*d"%(mantissa, exp_digits + 1, int(exp))


