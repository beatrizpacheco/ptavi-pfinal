#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa uaclient
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Cliente UDP simple.
"""
if len(sys.argv) != 4:
    sys.exit('Usage: python3 uaclient.py config method opcion')

CONFIG = sys.argv[1]
METHOD = sys.argv[2] #  Error si no es un metodo sip
OPCION = sys.argv[3] 
"""

class UAClientHandler(ContentHandler):

    def __init__ (self):
        self.list = []
        self.label = {'account': ['username', 'passwd'],
                      'uaserver': ['ip', 'puerto'],
                      'rtpaudio': ['puerto'],
                      'regproxy': ['ip', 'puerto'],
                      'log': ['path'],
                      'audio': ['path']}

    def startElement(self, name, attrs):
        dic = {}
        if name in self.label:
            dic['name'] = name
            for atributo in self.label[name]:
                dic[atributo] = attrs.get(atributo, "")
            self.list.append(dic)

    def get_tags(self):
        return(self.list)

if __name__ == "__main__":
    parser = make_parser()
    cHandler = UAClientHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open('ua.xml'))
    print(cHandler.get_tags())
    
    

"""
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP, PORT))

    if METHOD == 'INVITE' or METHOD == 'BYE':
        my_socket.send(bytes(METHOD + ' sip:' + MESSAGE.split(':')[0] +
                             ' SIP/2.0\r\n', 'utf-8') + b'\r\n')

    DATA = my_socket.recv(1024)
    print('Recibido -- ', data.decode('utf-8'))
    MESSAGE_RECEIVE = data.decode('utf-8').split(' ')
    for element in message_receive:
        if METHOD != 'BYE' and element == '200':
            my_socket.send(bytes('ACK sip:' + MESSAGE.split(':')[0] +
                                 ' SIP/2.0\r\n', 'utf-8') + b'\r\n')
    print("Terminando socket...")

print("Fin.")

"""
