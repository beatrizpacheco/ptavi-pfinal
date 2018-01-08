#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import os
import socket
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
            # Leyendo línea a línea lo que nos envían
            message= self.rfile.read().decode('utf-8')
            print(message)
            if not message:
                break
            method = message.split()[0]
            #if self.error(list_line_decode):
             #   self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            if method == 'INVITE' or method == 'invite':
                ip_emisor = message.split()[7]
                print('ip: ' + ip_emisor) #COMPROBACION
                port_emisor = message.split()[11]
                print('puerto: ' + port_emisor) #COMPROBACION
                #user_emisor = message.split()[6].split('=')[1]
                
                self.wfile.write(bytes("SIP/2.0 100 Trying\r\n\r\n" +
                                       "SIP/2.0 180 Ringing\r\n\r\n" +
                                       "SIP/2.0 200 OK\r\n\r\n" +
                                       '\r\n\r\n' + 
                                       'v=0\r\n' + 
                                       'o=' + USER + ' ' + IP_UASERVER + '\r\n' +
                                       's=misesion' + '\r\n' +
                                       't=0\r\n' +
                                       'm=audio ' + RTPAUDIO + ' RTP\r\n', 'utf-8'))
                
            elif method == 'ACK' or method == 'ack':
                ip_emisor = self.client_address[0]
                port_emisor = self.client_address[1]
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((ip_emisor, port_emisor))
                a_ejecutar = './mp32rtp -i ' + ip_emisor + ' -p ' + str(port_emisor) + ' < ' + AUDIO_FILE
                print('Vamos a ejecutar', a_ejecutar)
                os.system(a_ejecutar)
                print('creo que ya se ha acabado')
            elif method == 'BYE' or method == 'bye':
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
    USER = UAClientHandler.config['account_username']
    RTPAUDIO = UAClientHandler.config['rtpaudio_puerto']
    #Servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP_UASERVER, PORT_UASERVER), EchoHandler)
    print('listening...')
    try:
        SERV.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')


