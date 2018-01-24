#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Class (and main program) of the proxy-register server
"""

import hashlib
import os
import random
import socket
import socketserver
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import write_log


class ProxyHandler(ContentHandler):
    """
    method to read configuration information of the config file
    """
    config = {}

    def __init__(self):
        self.label = {"server": ["name", "ip", "puerto"],
                      "database": ["path", "passwdpath"],
                      "log": ["path"]}

    def startElement(self, name, attrs):
        if name in self.label:
            for atributo in self.label[name]:
                self.config[name + "_" + atributo] = attrs.get(atributo, "")

    def get_tags(self):
        return self.config

    def elparser(fich):
        parser = make_parser()
        pr_handler = ProxyHandler()
        parser.setContentHandler(pr_handler)
        parser.parse(open(fich))
        return pr_handler.get_tags()


def fich_passwords(user):
    """
    method to get the password of clients with password file
    """
    with open(PSSWD_PATH, "r") as fich:
        psswd = None  # ESTO NO SE SI ESTA BIEN O HAY QUE QUITARLO
        for line in fich:
            user_fich = line.split()[1]
            if user == user_fich:
                psswd = line.split()[3]
                break
        return psswd


def checking(nonce_user, user):
    """
    method to get the number result of hash function
    with password and nonce
    """
    function_check = hashlib.md5()
    function_check.update(bytes(str(nonce_user), "utf-8"))
    function_check.update(bytes(fich_passwords(user), "utf-8"))
    function_check.digest()
    return function_check.hexdigest()


def error(line):  # para el extra del error 400
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
        if 'SIP/2.0' not in line:
            fail = True
    except IndexError:
        fail = True
    return fail


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
                        str(self.dic_users[user][2]) + ', ' +
                        str(self.dic_users[user][3]) + '\r\n')
                fich.write(line)

    def expired(self):
        """
        method to check expiration of users
        """
        expired_users = []
        current_hour = time.time()
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
        while 1:
            message = self.rfile.read().decode('utf-8')
            if not message:
                break
            method = message.split()[0]
            # write receive
            write_log(LOG_FILE, 'receive', self.client_address[0],
                      self.client_address[1], message)
            print(message)
            if error(message.split()):
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")

            elif method == 'REGISTER' or method == 'register':
                user = message.split()[1].split(':')[1]
                ip_address = self.client_address[0]
                port_address = message.split()[1].split(':')[2]  # uaserver
                duration = message.split()[4]
                if user in self.dic_users:
                    if duration != '0':
                        # cambio expire
                        expire = time.time() + int(duration)
                        self.dic_users[user][3] = expire
                        # subo a base de datos
                        self.write_database(DB_PATH)

                    elif duration == '0':
                        del self.dic_users[user]

                    # envío 200ok
                    to_send = ('SIP/2.0 200 OK\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    # write send
                    write_log(LOG_FILE, 'send', ip_address,
                              self.client_address[1], to_send)

                else:
                    if message.split('\r\n')[2]:
                        if message.split()[5] == 'Authorization:':
                            # compruebo si el nonce coincide con mi nonce
                            client_response = message.split()[7][10:-1]
                            try:  # por si alguien envia nonce sin enviarlo yo
                                my_response = checking(self.dic_nonces[user],
                                                       user)
                                if client_response == my_response:
                                    self.dic_nonces[user]
                                    # añado usuario al dic
                                    time_regist = time.time()
                                    expire = time.time() + int(duration)
                                    self.dic_users[user] = [ip_address,
                                                            port_address,
                                                            time_regist,
                                                            expire]
                                    # subo a base de datos
                                    #self.write_database(DB_PATH)PROBAR A VER SI VA O NO VA
                                    # envío 200ok
                                    to_send = ('SIP/2.0 200 OK\r\n\r\n')
                                    self.wfile.write(bytes(to_send, 'utf-8'))
                                    # write send
                                    write_log(LOG_FILE, 'send', ip_address,
                                              self.client_address[1], to_send)
                                else:
                                    # error mal formado
                                    to_send = ('SIP/2.0 400 Bad Request' +
                                               '\r\n\r\n')
                                    self.wfile.write(bytes(to_send, 'utf-8'))
                                    # write send
                                    write_log(LOG_FILE, 'send', ip_address,
                                              self.client_address[1], to_send)
                            except KeyError:
                                to_send = ('SIP/2.0 404 User Not Found' +
                                           '\r\n\r\n')
                                self.wfile.write(bytes(to_send, 'utf-8'))
                                # write send
                                write_log(LOG_FILE, 'send', ip_address,
                                          self.client_address[1], to_send)
                    else:
                        # envío el nonce
                        nonce = random.randint(00000000, 99999999)
                        self.dic_nonces[user] = str(nonce)
                        to_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                   'WWW-Authenticate: Digest nonce="' +
                                   self.dic_nonces[user] + '"\r\n\r\n')
                        self.wfile.write(bytes(to_send, 'utf-8'))
                        # write send
                        write_log(LOG_FILE, 'send', ip_address,
                                  self.client_address[1], to_send)

            elif method == 'INVITE' or method == 'invite':
                # miro en mi dic si usuario emisor y receptor están
                user_emisor = message.split()[6].split('=')[1]
                user_receptor = message.split()[1].split(':')[1]
                if user_emisor in self.dic_users:
                    if user_receptor in self.dic_users:
                        ip_address_receptor = self.dic_users[user_receptor][0]
                        p_address_receptor = self.dic_users[user_receptor][1]
                        ip_address_emisor = self.dic_users[user_emisor][0]
                        port_address_emisor = self.dic_users[user_emisor][1]
                        try:
                            with socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM) as my_socket:
                                my_socket.setsockopt(socket.SOL_SOCKET,
                                                     socket.SO_REUSEADDR, 1)
                                my_socket.connect((ip_address_receptor,
                                                  int(p_address_receptor)))
                                my_socket.send(bytes(message, 'utf-8'))
                                # write send
                                write_log(LOG_FILE, 'send',
                                          ip_address_receptor,
                                          int(p_address_receptor), message)
                                DATA = my_socket.recv(1024)
                                # write receive
                                write_log(LOG_FILE, 'receive',
                                          ip_address_receptor,
                                          int(p_address_receptor),
                                          DATA.decode('utf-8'))
                            self.wfile.write(bytes(DATA.decode('utf-8'),
                                                   'utf-8'))
                            # write send
                            write_log(LOG_FILE, 'send', ip_address_emisor,
                                      int(port_address_emisor),
                                      DATA.decode('utf-8'))
                        except ConnectionRefusedError:
                            to_send = ("Error: no server listening at " +
                                       ip_address_receptor + " port " +
                                       p_address_receptor)
                            print(to_send)
                            write_log(LOG_FILE, 'error', None, None, to_send)
                            to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                            self.wfile.write(bytes(to_send, 'utf-8'))
                            # write send
                            write_log(LOG_FILE, 'send', ip_address_emisor,
                                      int(port_address_emisor), to_send)
                else:
                    # user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    # write send
                    write_log(LOG_FILE, 'send', self.client_address[0],
                              self.client_address[1], to_send)

            elif method == 'BYE' or method == 'bye':
                method = message.split()[0]
                # miro en mi dic si usuario está
                user_receptor = message.split()[1].split(':')[1]
                if user_receptor in self.dic_users:
                    ip_address_receptor = self.dic_users[user_receptor][0]
                    port_address_receptor = self.dic_users[user_receptor][1]
                    try:
                        with socket.socket(socket.AF_INET,
                                           socket.SOCK_DGRAM) as my_socket:
                            my_socket.setsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR, 1)
                            my_socket.connect((ip_address_receptor,
                                              int(port_address_receptor)))
                            my_socket.send(bytes(message, 'utf-8'))
                            # write send
                            write_log(LOG_FILE, 'send', ip_address_receptor,
                                      int(port_address_receptor), message)
                            DATA = my_socket.recv(1024)
                            # write receive
                            write_log(LOG_FILE, 'receive', ip_address_receptor,
                                      int(port_address_receptor),
                                      DATA.decode('utf-8'))
                        self.wfile.write(bytes(DATA.decode('utf-8'), 'utf-8'))
                        # write send
                        write_log(LOG_FILE, 'send', self.client_address[0],
                                  self.client_address[1], DATA.decode('utf-8'))
                    except ConnectionRefusedError:
                        to_send = ("Error: no server listening at " +
                                   ip_address_receptor + " port " +
                                   port_address_receptor)
                        print(to_send)
                        write_log(LOG_FILE, 'error', None, None, to_send)
                        to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                        self.wfile.write(bytes(to_send, 'utf-8'))
                        # write send
                        write_log(LOG_FILE, 'send', self.client_address[0],
                                  self.client_address[1], to_send)
                else:
                    # user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    # write send
                    write_log(LOG_FILE, 'send', self.client_address[0],
                              self.client_address[1], to_send)

            elif method == 'ACK' or method == 'ack':
                method = message.split()[0]
                user_emisor = message.split()[1].split(':')[1]
                # if user in mi dic:
                if user_emisor in self.dic_users:
                    ip_address_emisor = self.dic_users[user_emisor][0]
                    port_address_emisor = self.dic_users[user_emisor][1]
                    try:
                        with socket.socket(socket.AF_INET,
                                           socket.SOCK_DGRAM) as my_socket:
                            my_socket.setsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR, 1)
                            my_socket.connect((ip_address_emisor,
                                              int(port_address_emisor)))
                            my_socket.send(bytes(message, 'utf-8'))
                            # write send
                            write_log(LOG_FILE, 'send', ip_address_emisor,
                                      int(port_address_emisor), message)
                    except ConnectionRefusedError:
                        to_send = ("Error: no server listening at " +
                                   ip_address_emisor + " port " +
                                   port_address_emisor)
                        print(to_send)
                        write_log(LOG_FILE, 'error', None, None, to_send)
                        to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                        self.wfile.write(bytes(to_send, 'utf-8'))
                        # write send
                        write_log(LOG_FILE, 'send', self.client_address[0],
                                  self.client_address[1], to_send)

                else:
                    # user not found
                    to_send = ('SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    # write send
                    write_log(LOG_FILE, 'send', self.client_address[0],
                              self.client_address[1], to_send)

            else:
                # metodo no permitido
                to_send = ('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                self.wfile.write(bytes(to_send, 'utf-8'))
                # write send
                write_log(LOG_FILE, 'send', self.client_address[0],
                          self.client_address[1], to_send)

            print(self.dic_users)
            self.write_database(DB_PATH)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 proxy_registrar.py config")
    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    print(ProxyHandler.elparser(CONFIG))  # comprobacion, no hace falta

    # Doy valor a las variables segun la info del xml
    if ProxyHandler.config["server_ip"] is None:
        IP_SERVER = "127.0.0.1"
    else:
        IP_SERVER = ProxyHandler.config['server_ip']
    NAME_SERVER = ProxyHandler.config['server_name']
    PORT_SERVER = int(ProxyHandler.config['server_puerto'])
    DB_PATH = ProxyHandler.config['database_path']
    PSSWD_PATH = ProxyHandler.config['database_passwdpath']
    LOG_FILE = ProxyHandler.config['log_path']

    # write starting
    write_log(LOG_FILE, 'open', None, None, None)
    SERV = socketserver.UDPServer((IP_SERVER, PORT_SERVER),
                                  ProxyRegisterHandler)
    print("Server " + NAME_SERVER + " listening at port " +
          str(PORT_SERVER) + "...")
    try:
        SERV.serve_forever()  # Esperando alguna conexion infinitamente
    except KeyboardInterrupt:
        print("Finalizado servidor")
        # write fin
        write_log(LOG_FILE, 'fin', None, None, None)
