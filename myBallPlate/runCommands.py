from sys import argv
import pexpect




children = []
for i in range(3, len(argv)):
    children.append(pexpect.spawn('/bin/bash'))
    children[len(children) - 1].sendline(argv[i])
    print(argv[i])

import time

time.sleep(int(argv[1]))
for child in children:
    child.sendcontrol('c')
    child.sendline('exit')
    child.expect(pexpect.EOF)

    
#    if len(children) != 0:
#        open(argv[2] + '.txt', 'w').write(children[len(children) - 1].read())


