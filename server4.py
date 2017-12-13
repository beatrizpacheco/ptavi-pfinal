#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import json
import socketserver
import sys
import time

if len(sys.argv) != 2:
    sys.exit("Usage: python3 server.py puerto")
PORT = int(sys.argv[1])


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    dic_users = {}

    def json2registered(self):
        """
        method to view clients of json file
        """
        try:
            with open('registered.json', 'r') as fich:
                self.dic_users = json.load(fich)
                self.expired()
        except (NameError, FileNotFoundError):
            pass

    def register2json(self):
        """
        method to save the users in the json file
        """
        self.expired()
        json.dump(self.dic_users, open('registered.json', "w"))

    def expired(self):
        """
        method to check expiration of users
        """
        expired_users = []
        current_hour = time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.gmtime(time.time()))
        for user in self.dic_users:
            if self.dic_users[user][1] < current_hour:
                expired_users.append(user)
        for user in expired_users:
            del self.dic_users[user]

    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        self.json2registered()
        self.expired()
        for line in self.rfile:
            message = line.decode('utf-8').split()
            if message and message[0] == 'REGISTER':
                user = message[1][4:]
                ip_address = self.client_address[0]
            if message and message[0] == 'Expires:':
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
            print(line.decode('utf-8'), end='')
        print(self.dic_users)
        self.register2json()

if __name__ == "__main__":
    serv = socketserver.UDPServer(('', PORT), SIPRegisterHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()  # Esperando alguna conexion infinitamente
    except KeyboardInterrupt:
        print("Finalizado servidor")
