import socket
import os

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect(("garage.local",80))
    s.close()
    print "successfully connected."
except Exception, e:
    print "failed to connect, restarting avahi daemon: ", str(e)
    os.system("service avahi-daemon restart")
    pass
