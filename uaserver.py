#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import os
import socketserver
import sys
from uaclient import UAClientHandler

if __name__ == "__main__":
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    if len(sys.argv) < 2:
        print('Usage: python3 uaserver.py config')
    UAClientHandler.elparser()
    #Servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP_UASERVER, PORT_UASERVER))
    print('listening...')
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')


