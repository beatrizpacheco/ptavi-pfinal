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
    LISTA = ['INVITE', 'ACK', 'BYE']

    def error(self, line):
        """
        method to verify if message is correct
        """
        fail = False
        try:
            if len(line) != 3:
                fail = True
            if line[1][0:4] != 'sip:':
                fail = True
            if '@' not in line[1]:
                fail = True
            if ':' not in line[1]:
                fail = True
            if 'SIP/2.0\r\n\r\n' not in line[2]:
                fail = True
        except IndexError:
            fail = True
        return fail

    def handle(self):
        """
        handle method of the server class
        """
        while 1:
            # Leyendo línea a línea lo que nos envía el servidor
            line = self.rfile.read()
            print(line.decode('utf-8'))
            if not line:
                break
            list_line_decode = line.decode('utf-8').split(' ')
            method = list_line_decode[0]
            if self.error(list_line_decode):
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            elif method == 'INVITE':
                self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n" +
                                 b"SIP/2.0 180 Ringing\r\n\r\n" +
                                 b"SIP/2.0 200 OK\r\nContent-Type: application/sdp\r\n\r\n" + 
                                 'v=0\r\n' + 
                                 'o=origen\r\n' +
                                 's=misesion\r\n' +
                                 't=0\r\n' +
                                 'm=audio puerto RTP\r\n')
            elif method == 'ACK':
                aEjecutar = './mp32rtp -i 127.0.0.1 -p 23032 < ' + AUDIO_FILE
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
            elif method == 'BYE':
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            elif method not in self.LISTA:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    print(UAClientHandler.elparser(CONFIG))
    
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    AUDIO_FILE = UAClientHandler.config['audio_path']
    
    #Servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP_UASERVER, PORT_UASERVER), EchoHandler)
    print('listening...')
    try:
        SERV.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')


