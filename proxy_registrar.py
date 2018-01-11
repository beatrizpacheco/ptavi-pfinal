#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Class (and main program) of the proxy-register server
"""

import hashlib
import json
import os
import random
import socket
import socketserver
import sys
import time
from uaclient import write_log
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class ProxyHandler(ContentHandler):
    """
    method to read configuration information of the config file
    """
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

def fich_passwords(user):
    """
    method to get the password of clients with password file
    """
    with open(PSSWD_PATH, "r") as fich:
        psswd = None #ESTO NO SE SI ESTA BIEN O HAY QUE QUITARLO
        for line in fich:
            user_fich = line.split()[1]
            if user == user_fich:
                psswd = line.split()[3]
                print('LA CONTRASEÑA EN EL FICH_PASSWD ES : "' + psswd + '"') #COMPROBACION
                break
        return psswd

def checking(nonce_user, user):
    """
    method to get the number result of hash function
    with password and nonce
    """
    function_check = hashlib.md5()
    function_check.update(bytes(str(nonce_user), "utf-8"))#NO SE SI HACE FALTA PASAR A STRING
    print('EL PUTO NONCE ES : "' + str(nonce_user) + '"') #COMPROBACION
    function_check.update(bytes(fich_passwords(user), "utf-8"))
    print('LA CONTRASEÑA ES : "' + fich_passwords(user) + '"') #COMPROBACION
    function_check.digest() #no sé si esto hace falta o directamente hex
    print('RESPONSE PROXY: ' + function_check.hexdigest()) #COMPROBACION
    return function_check.hexdigest()


class ProxyRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Proxy-Register server class
    """
    dic_users = {}
    dic_nonces = {}
    
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

    def read_database(self, path):#Para el extra de leer del fichero
        """
        method to look for the users in the database
        """
        pass
    
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

    def error(self, line):#para el extra del error 400
        """
        method to verify if message is correct
        """
        fail = False
        try:
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
        (all requests will be handled by this method)
        """
        while 1:
            #self.json2registered()
            message= self.rfile.read().decode('utf-8')
            if not message:
                break
            print('lineeeeeeeeee ' + message)#COMPROBACION
            method = message.split()[0]
            print('métodooooooo ' + method)#COMPROBACION
            #write receive
            write_log(LOG_FILE, 'receive', self.client_address[0], self.client_address[1], message)
            
            #if self.error(message):
             #   self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            
            if (method == 'REGISTER' or method == 'register'):
                user = message.split()[1].split(':')[1]
                ip_address = self.client_address[0]
                port_address = message.split()[1].split(':')[2] #Este es el del uaserver
                duration = message.split()[4]
                print(user + ' ' + ip_address + ' ' + str(port_address))#COMPROBACION
                if user in self.dic_users:
                    print('el usuario está en el dic') #COMPROBACION
                    if duration != '0':
                        #cambio expire
                        expire =  time.strftime('%Y-%m-%d %H:%M:%S',
                                                    time.gmtime(time.time() +
                                                    int(duration)))
                        self.dic_users[user][3] = expire
                        #subo a base de datos
                        self.write_database(DB_PATH)
                        
                    elif duration == '0':
                        del self.dic_users[user]
                    
                    #envío 200ok
                    to_send = ('SIP/2.0 200 OK\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', ip_address, self.client_address[1], to_send)

                else:
                    print('el usuario NO está en el dic') #COMPROBACION
                    if message.split('\r\n')[2]:
                        print('el mensaje tiene tercera linea') #COMPROBACION
                        if message.split()[5] == 'Authorization:':
                            print('el mensaje tiene Authorization:') #COMPROBACION
                            #compruebo si el nonce coincide con mi nonce
                            client_response = message.split()[7][10:-1]
                            print('CLIENT RESPONSE : ' + client_response) #COMPROBACION
                            #if su_nonce==mi_nonce:
                            try:#por si alguien envia nonce sin enviarlo yo
                                my_response = checking(self.dic_nonces[user], user)
                                print('MY RESPONSE : ' + my_response) #COMPROBACION
                                if client_response == my_response:
                                    print('coinciden nonces') #COMPROBACION
                                    #borro del diccionario de nonces el que acabo de ver que está bein
                                    self.dic_nonces[user]
                                    #añado usuario al dic
                                    time_regist = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                time.gmtime(time.time()))
                                    expire =  time.strftime('%Y-%m-%d %H:%M:%S',
                                                            time.gmtime(time.time() +
                                                            int(duration)))
                                    #time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(time.time()+3600))
                                    #Esto para cuando me de una hora menos que la real
                                    self.dic_users[user] = [ip_address, port_address,
                                                            time_regist, expire]
                                    #subo a base de datos
                                    self.write_database(DB_PATH)
                                    #envío 200ok
                                    to_send = ('SIP/2.0 200 OK\r\n\r\n')
                                    self.wfile.write(bytes(to_send, 'utf-8'))
                                    #write send
                                    write_log(LOG_FILE, 'send', ip_address, self.client_address[1], to_send)
                                #else:
                                else:
                                    print('NO coinciden nonces') #COMPROBACION
                                    #error mal formado
                                    to_send = ('SIP/2.0 400 Bad Request\r\n\r\n')
                                    self.wfile.write(bytes(to_send, 'utf-8'))
                                    #write send
                                    write_log(LOG_FILE, 'send', ip_address, self.client_address[1], to_send)
                            except KeyError:
                                to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                                self.wfile.write(bytes(to_send, 'utf-8'))
                                #write send
                                write_log(LOG_FILE, 'send', ip_address, self.client_address[1], to_send)
                    else:
                        print('el mensaje NO tiene tercera linea') #COMPROBACION
                        #envío el nonce
                        nonce = random.randint(00000000, 99999999)
                        self.dic_nonces[user] = str(nonce)
                        to_send = ('SIP/2.0 401 Unauthorized\r\n' + 
                                  'WWW-Authenticate: Digest nonce="' +
                                  self.dic_nonces[user] + '"\r\n\r\n')
                        self.wfile.write(bytes(to_send, 'utf-8'))
                        #write send
                        write_log(LOG_FILE, 'send', ip_address, self.client_address[1], to_send)
                    
                
            elif (method == 'INVITE' or method == 'invite'):
                method = message.split()[0]#no hace falta
                print('métodooooooo ' + method)#COMPROBACION
                #miro en mi dic si usuario emisor y receptor están
                user_emisor = message.split()[6].split('=')[1]
                user_receptor = message.split()[1].split(':')[1]
                #print(user + ' ' + ip_address + ' ' + str(port_address))#COMPROBACION
                #print('IP Y PUERTO DEL QUE MANDA EL INVITE' + 
                 #     self.client_address[0] + str(self.client_address[1]))#COMPROBACION
                print('User Emisor: ' + user_emisor) #COMPROBACION
                print('User Receptor: ' + user_receptor) #COMPROBACION
                print('VOY A COMPROBAR SI LOS USUARIOS EMISOR Y RECEPTOR LOS TENGO EN MI DIC') #COMPROBACION
                if user_emisor in self.dic_users and user_receptor in self.dic_users:
                    print('BIEEEEEN LOS TENGO EN MI DIC') #COMPROBACION
                #if user in mi dic:
                    #cojo datos del usuario receptor (ip y puerto)
                    #self.dic_users[user] = [ip_address, port_address,time_regist, expire]
                    ip_address_receptor = self.dic_users[user_receptor][0]
                    port_address_receptor = self.dic_users[user_receptor][1]
                    ip_address_emisor = self.dic_users[user_emisor][0]
                    port_address_emisor = self.dic_users[user_emisor][1]
                    print('User Emisor: ' + user_emisor) #COMPROBACION
                    print('ip Emisor: ' + ip_address_emisor) #COMPROBACION
                    print('port Emisor: ' + str(port_address_emisor)) #COMPROBACION
                    print('User Receptor: ' + user_receptor) #COMPROBACION
                    print('ip Emisor: ' + ip_address_receptor) #COMPROBACION
                    print('port Emisor: ' + str(port_address_receptor)) #COMPROBACION
                    #reenvio invite (abro socket con el receptor)
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_address_receptor, int(port_address_receptor)))
                        my_socket.send(bytes(message, 'utf-8'))
                        #write send
                        write_log(LOG_FILE, 'send', ip_address_receptor, int(port_address_receptor), message)
                        DATA = my_socket.recv(1024)
                        #
                        print('LA RESPUESTA DEL RECEPTOR EN EL INVITE ES: ' + DATA.decode('utf-8'))
                        #write receive
                        write_log(LOG_FILE, 'receive', ip_address_receptor, int(port_address_receptor), DATA.decode('utf-8'))
                    self.wfile.write(bytes(DATA.decode('utf-8'), 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', ip_address_emisor, int(port_address_emisor), DATA.decode('utf-8'))
                    #else
                else:
                    print('FUUUUUUUCK NO LOS TENGO EN MI DIC') #COMPROBACION
                    #user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', self.client_address[0], self.client_address[1], to_send)
            
            elif (method == 'BYE' or method == 'bye'):
                method = message.split()[0]
                print('métodooooooo ' + method)#COMPROBACION
                #miro en mi dic si usuario está
                user_receptor = message.split()[1].split(':')[1]
                print('User Receptor: ' + user_receptor) #COMPROBACION
                print('VOY A COMPROBAR SI LOS USUARIOS LOS TENGO EN MI DIC') #COMPROBACION
                if user_receptor in self.dic_users:
                    print('BIEEEEEN LOS TENGO EN MI DIC') #COMPROBACION
                #if user in mi dic:
                    #cojo datos del usuario receptor (ip y puerto)
                    #self.dic_users[user] = [ip_address, port_address,time_regist, expire]
                    ip_address_receptor = self.dic_users[user_receptor][0]
                    port_address_receptor = self.dic_users[user_receptor][1]
                    print('User Receptor: ' + user_receptor) #COMPROBACION
                    print('ip Emisor: ' + ip_address_receptor) #COMPROBACION
                    print('port Emisor: ' + str(port_address_receptor)) #COMPROBACION
                    #reenvio bye (abro socket con el receptor)
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_address_receptor, int(port_address_receptor)))
                        my_socket.send(bytes(message, 'utf-8'))
                        #write send
                        write_log(LOG_FILE, 'send', ip_address_receptor, int(port_address_receptor), message)
                        DATA = my_socket.recv(1024)
                        #
                        #write receive
                        write_log(LOG_FILE, 'receive', ip_address_receptor, int(port_address_receptor), DATA.decode('utf-8'))
                        print('LA RESPUESTA DEL RECEPTOR EN EL INVITE ES: ' + DATA.decode('utf-8'))
                    self.wfile.write(bytes(DATA.decode('utf-8'), 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', self.client_address[0], self.client_address[1], DATA.decode('utf-8'))
                    #else
                else:
                    print('FUUUUUUUCK NO LOS TENGO EN MI DIC') #COMPROBACION
                    #user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', self.client_address[0], self.client_address[1], to_send)
                
            elif (method == 'ACK' or method == 'ack'):
                method = message.split()[0]
                print('métodooooooo ' + method)#COMPROBACION
                user_emisor = message.split()[1].split(':')[1]
                #if user in mi dic:
                if user_emisor in self.dic_users:
                    ip_address_emisor = self.dic_users[user_emisor][0]
                    port_address_emisor = self.dic_users[user_emisor][1]
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        my_socket.connect((ip_address_emisor, int(port_address_emisor)))
                        my_socket.send(bytes(message, 'utf-8'))
                        #write send
                        write_log(LOG_FILE, 'send', ip_address_emisor, int(port_address_emisor), message)
                        
                else:
                    print('FUUUUUUUCK NO LOS TENGO EN MI DIC') #COMPROBACION
                    #user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    #write send
                    write_log(LOG_FILE, 'send', self.client_address[0], self.client_address[1], to_send)
                
            else:
                #metodo no permitido
                to_send = ('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                self.wfile.write(bytes(to_send, 'utf-8'))
                #write send
                write_log(LOG_FILE, 'send', self.client_address[0], self.client_address[1], to_send)
                
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
    PSSWD_PATH = ProxyHandler.config['database_passwdpath']
    LOG_FILE = ProxyHandler.config['log_path']
       
    #write starting
    write_log(LOG_FILE, 'open', None, None, None)
    SERV = socketserver.UDPServer((IP_SERVER, PORT_SERVER), ProxyRegisterHandler)
    print("Server " + NAME_SERVER + " listening at port " + str(PORT_SERVER) + "...")
    try:
        SERV.serve_forever()  # Esperando alguna conexion infinitamente
    except KeyboardInterrupt:
        print("Finalizado servidor")
        #write fin
        write_log(LOG_FILE, 'fin', None, None, None)
