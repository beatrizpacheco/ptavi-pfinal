#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import json
import os
import socketserver
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class proxyHandler(ContentHandler):

    config = {}

    def __init__(self):
        self.label = {"server": ["name", "ip", "puerto"],
                      "database": ["path","passwdpath"],
                      "log": ["path"]}

    def startElement(self, name, attrs):
        if name in self.label:
            for atributo in self.label[name]:
                self.config[name + "_" + atributo] = attrs.get(atributo, "")

    def get_tags(self):
        return (self.config)
        
    def elparser(fich):
        parser = make_parser()
        prHandler = proxyHandler()
        parser.setContentHandler(prHandler)
        parser.parse(open(fich))
        return(prHandler.get_tags())


class ProxyRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    dic_users = {}
    """
    Aquí iría la movida del log y de echar a los clientes expirados#############
    """
    def user_register(self, fich):
        """
        Comprueba si usuario registrado o no
        """
        
    
    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        for line in self.rfile:
            message = line.decode('utf-8').split()
            if message and (message[0] == 'REGISTER' or
                            message[0] == 'register'):
                print('recibo un register')
                user = message[1][4:]
                ip_address = self.client_address[0]
            if message and message[0] == 'Expires:':
                print('linea del expires')
                if message[1] != '0':
                    expire = time.strftime('%Y-%m-%d %H:%M:%S',
                                           time.gmtime(time.time() +
                                                       int(message[1])))
                    self.dic_users[user] = [ip_address, expire]
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                elif message[1] == '0':
                    try:
                        del self.dic_users[user]
                        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                    except KeyError:
                        self.wfile.write(b'SIP/2.0 404 User '
                                         b'Not Found\r\n\r\n')
            if message and (message[0] == 'INVITE' or
                            message[0] == 'invite'):
                print('recibo un invite')
                #voy guardando el invite con sdp en el nuevo mensaje
                #abro socket con el cliente y le envio el mensaje
            #print(line.decode('utf-8'), end='')
        print(self.dic_users)
        

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 proxy_registrar.py config")
    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    print(proxyHandler.elparser(CONFIG))
    
    #Doy valor a las variables segun la info del xml
    if proxyHandler.config["server_ip"] == None:
        IP_SERVER = "127.0.0.1"
    else:
        IP_SERVER = proxyHandler.config['server_ip']
    NAME_SERVER = proxyHandler.config['server_name']
    PORT_SERVER = int(proxyHandler.config['server_puerto'])
    DB_PATH = proxyHandler.config['database_path']
       
        
    serv = socketserver.UDPServer((IP_SERVER, PORT_SERVER), ProxyRegisterHandler)
    print("Server " + NAME_SERVER + " listening at port " + str(PORT_SERVER) + "...")
    try:
        serv.serve_forever()  # Esperando alguna conexion infinitamente
    except KeyboardInterrupt:
        print("Finalizado servidor")
