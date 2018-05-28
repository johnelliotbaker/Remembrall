import re
from io import BytesIO


def bin2int(b):
    return int.from_bytes(b, byteorder='big')

def int2bins(i):
    return '{:032b}'.format(i)

def findLeadingZeros(bins):
    match = re.findall('[0]+[^0]', bins)[0]
    return len(match)

def getEbmlType(n):
    if n < 16:
        return 1

def doFour(f):
    a = f.read(4)
    i = bin2int(a)
    bins = int2bins(i)
    print(bins)
    k = findLeadingZeros(bins)
    print(k)
    return k


a = b'\x1a\x45\xdf\xa3'
a = b'\x67\xc8'






filename = r'E:\Drama\en\Movies\a.mkv'
f = open(filename, 'rb')

n = doFour(f)
f.seek(-4, 1)
n = doFour(f)
f.seek(-4, 1)
n = doFour(f)



f.close()
