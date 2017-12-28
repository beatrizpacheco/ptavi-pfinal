#!#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa uaclient
"""

import os
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Cliente UDP simple.


class UAClientHandler(ContentHandler):

    config = {}

    def __init__ (self):
        self.label = {'account': ['username', 'passwd'],
                      'uaserver': ['ip', 'puerto'],
                      'rtpaudio': ['puerto'],
                      'regproxy': ['ip', 'puerto'],
                      'log': ['path'],
                      'audio': ['path']}

    def startElement(self, name, attrs):
        if name in self.label:
            for atributo in self.label[name]:
                self.config[name + "_" + atributo] = attrs.get(atributo, "")

    def get_tags(self):
        return(self.config)
        
    def elparser(fich):
        parser = make_parser()
        uaHandler = UAClientHandler()
        parser.setContentHandler(uaHandler)
        parser.parse(open(fich))
        return(uaHandler.get_tags())

if __name__ == "__main__":

    if len(sys.argv) != 4:
        sys.exit('Usage: python3 uaclient.py config method opcion')

    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    METHOD = sys.argv[2] #  Error si no es un metodo sip
    OPCION = sys.argv[3]
    print(UAClientHandler.elparser(CONFIG))
    
    #Doy valor a las variables segun la info del xml
    if UAClientHandler.config["regproxy_ip"] == None:
        IP_PROXY = "127.0.0.1"
    else:
        IP_PROXY = UAClientHandler.config['regproxy_ip']
    PORT_PROXY = int(UAClientHandler.config['regproxy_puerto'])
    USER = UAClientHandler.config['account_username']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    RTPAUDIO = UAClientHandler.config['rtpaudio_puerto']
    
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto 
    # del servidor regproxy
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY, PORT_PROXY))

        if (METHOD == 'REGISTER' or METHOD == 'register'):
            my_socket.send(bytes(METHOD + ' sip:' + USER + ':' +
                                 str(PORT_UASERVER) + ' SIP/2.0\r\nExpires: ' +
                                 OPCION + '\r\n\r\n', 'utf-8') + b'\r\n')
        #DESPUES DE ESTO ME ENVIARÁN UN MENSAJE DE AUTENTICACION
        if (METHOD == 'INVITE' or METHOD == 'invite'):
            my_socket.send(bytes(METHOD + ' sip:' + OPCION  +
                                 ' SIP/2.0\r\nContent-Type: application/sdp' + 
                                 '\r\n\r\n' + 
                                 'v=0\r\n' + 
                                 'o=' + USER + '\r\n' +
                                 's=misesion\r\n' +
                                 't=0\r\n' +
                                 'm=audio ' + RTPAUDIO + ' RTP\r\n',
                                 'utf-8') + b'\r\n')
        
        
        if (METHOD == 'BYE' or METHOD == 'bye'):
            my_socket.send(bytes(METHOD + ' sip:' + OPCION  +
                                 ' SIP/2.0\r\n', 'utf-8') + b'\r\n')
"""
        data = my_socket.recv(1024)
        print('Recibido -- ', data.decode('utf-8'))
        MESSAGE_RECEIVE = data.decode('utf-8').split(' ')
        for element in message_receive:
            if METHOD != 'BYE' and element == '200':
                my_socket.send(bytes('ACK sip:' + MESSAGE.split(':')[0] +
                                     ' SIP/2.0\r\n', 'utf-8') + b'\r\n')
        print("Terminando socket...")

    print("Fin.")
"""
