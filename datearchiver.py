import sys

with open('dates.txt','r') as f:
	data = f.read().splitlines(True)
with open('dates.txt', 'w') as fout:
    fout.writelines(data[1:])