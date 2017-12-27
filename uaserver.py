#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import os
import socketserver
import sys
from uaclient import UAClientHandler

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    CONFIG = sys.argv[1]
    print(UAClientHandler.elparser(CONFIG))
#    print(UAClientHandler.get_tags(UAClientHandler))
    
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    
    #Servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP_UASERVER, PORT_UASERVER), EchoHandler)
    print('listening...')
    try:
        SERV.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')


