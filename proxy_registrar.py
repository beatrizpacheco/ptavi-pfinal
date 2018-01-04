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


class ProxyHandler(ContentHandler):

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
        prHandler = ProxyHandler()
        parser.setContentHandler(prHandler)
        parser.parse(open(fich))
        return(prHandler.get_tags())


class ProxyRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    dic_users = {}
    """
    Aquí iría la movida del log
    """

    def write_database(self, path):
        """
        method to save the users in the database
        """
        self.expired()
        with open(path, "w") as fich:
            for user in self.dic_users:
                line = (user + ', ' + self.dic_users[user][0] + ', ' + 
                       str(self.dic_users[user][1]) + ', ' +
                       self.dic_users[user][2] + ', ' + 
                       self.dic_users[user][3] + '\r\n')
                fich.write(line)

    
    def expired(self):
        """
        method to check expiration of users
        """
        expired_users = []
        current_hour = time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.gmtime(time.time()))
        for user in self.dic_users:
            if self.dic_users[user][3] < current_hour:
                expired_users.append(user)
        for user in expired_users:
            del self.dic_users[user]

    
    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        #self.json2registered()
        message= self.rfile.read().decode('utf-8')
        print('lineeeeeeeeee ' + message)#COMPROBACION
        method = message.split()[0]
        print('métodooooooo ' + method)#COMPROBACION
        if (method == 'REGISTER' or method == 'register'):
            user = message.split()[1].split(':')[1]
            ip_address = self.client_address[0]
            port_address = self.client_address[1]
            print(user + ' ' + ip_address + ' ' + str(port_address))#COMPROBACION
            if user in self.dic_users:
                pass
                #cambio expire
                #envío 200ok
            else:
                if message.split('\r\n')[2]:
                    if message.split()[5] == 'Authorization:':
                        pass
                        #compruebo si el nonce coincide con mi nonce
                        #if su_nonce==mi_nonce:
                            #añado usuario al dic y 200ok
                        #else:
                            #error mal formado o no autorizado o algo
                    else:
                        pass
                        #envío el nonce
                
            
        elif (method == 'INVITE' or method == 'invite'):
            pass
            #miro en mi dic si usuario está
            #if user in mi dic:
                #reenvio invite
            #else
                #user not found
        elif (method == 'BYE' or method == 'bye'):
            pass
            #miro en mi dic si usuario está
            #if user in mi dic:
                #lo borro del dic
            #else
                #user not found
        elif (method == 'ACK' or method == 'ack'):
            pass
            #no sé si esta es necesaria
        else:
            pass
            #error mal formado
            
            
        print(self.dic_users)
        self.write_database(DB_PATH)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 proxy_registrar.py config")
    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    print(ProxyHandler.elparser(CONFIG))
    
    #Doy valor a las variables segun la info del xml
    if ProxyHandler.config["server_ip"] == None:
        IP_SERVER = "127.0.0.1"
    else:
        IP_SERVER = ProxyHandler.config['server_ip']
    NAME_SERVER = ProxyHandler.config['server_name']
    PORT_SERVER = int(ProxyHandler.config['server_puerto'])
    DB_PATH = ProxyHandler.config['database_path']
       
        
    serv = socketserver.UDPServer((IP_SERVER, PORT_SERVER), ProxyRegisterHandler)
    print("Server " + NAME_SERVER + " listening at port " + str(PORT_SERVER) + "...")
    try:
        serv.serve_forever()  # Esperando alguna conexion infinitamente
    except KeyboardInterrupt:
        print("Finalizado servidor")
