#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Class (and main program) of the uaserver
"""

import os
import socket
import socketserver
import sys
from uaclient import UAClientHandler, write_log
from proxy_registrar import error, correct_ip, correct_port


class UAServerHandler(socketserver.DatagramRequestHandler):
    """
    UAServer class
    """
    LISTA = ['INVITE', 'ACK', 'BYE']
    dic_rtp = {}

    def look_for(self, ip):
        """
        method to look for the port of user
        """
        for user in self.dic_rtp:
            print(user)
            if ip == user:
                port = self.dic_rtp[user]
                break
        return port
        del self.dic_rtp[user]

    def handle(self):
        """
        handle method of the server class
        """
        while 1:
            # Leyendo línea a línea lo que nos envían
            message = self.rfile.read().decode('utf-8')
            print(message)
            if not message:
                break
            method = message.split()[0]
            # write receive
            write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY, message)
            if error(message.split()):  
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            elif method == 'INVITE' or method == 'invite':
                ip_emisor = message.split()[7]
                port_emisor = message.split()[11]
                self.dic_rtp[ip_emisor] = port_emisor
                to_send = ("SIP/2.0 100 Trying\r\n\r\n" +
                           "SIP/2.0 180 Ringing\r\n\r\n" +
                           "SIP/2.0 200 OK\r\n" +
                           "Content-Type: application/sdp" +
                           '\r\n\r\n' +
                           'v=0\r\n' +
                           'o=' + USER + ' ' + IP_UASERVER + '\r\n' +
                           's=misesion' + '\r\n' +
                           't=0\r\n' +
                           'm=audio ' + RTPAUDIO + ' RTP\r\n')
                self.wfile.write(bytes(to_send, 'utf-8'))
                # write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)

            elif method == 'ACK' or method == 'ack':
                ip_emisor = self.client_address[0]
                port_emisor = self.look_for(ip_emisor)
                a_ejecutar = ('./mp32rtp -i ' + ip_emisor + ' -p ' +
                              str(port_emisor) + ' < ' + AUDIO_FILE)
                print('Vamos a ejecutar', a_ejecutar)
                os.system(a_ejecutar)
                print('creo que ya se ha acabado')
                # write send
                write_log(LOG_FILE, 'send', ip_emisor, port_emisor,
                          ('Vamos a ejecutar' + a_ejecutar))
            elif method == 'BYE' or method == 'bye':
                to_send = ('SIP/2.0 200 OK\r\n\r\n')
                # write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)
                self.wfile.write(bytes(to_send, 'utf-8'))
            elif method not in self.LISTA:
                to_send = ('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                self.wfile.write(bytes(to_send, 'utf-8'))
                # write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    print(UAClientHandler.elparser(CONFIG))
    if UAClientHandler.config["regproxy_ip"] is None:
        IP_PROXY = "127.0.0.1"
    else:
        IP_PROXY = UAClientHandler.config['regproxy_ip']
    PORT_PROXY = int(UAClientHandler.config['regproxy_puerto'])
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    AUDIO_FILE = UAClientHandler.config['audio_path']
    USER = UAClientHandler.config['account_username']
    RTPAUDIO = UAClientHandler.config['rtpaudio_puerto']
    LOG_FILE = UAClientHandler.config['log_path']

    # write starting
    write_log(LOG_FILE, 'open', None, None, None)
    # Servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP_UASERVER, PORT_UASERVER),
                                  UAServerHandler)
    print('listening...')
    try:
        SERV.serve_forever()
    except KeyboardInterrupt:
        # write fin
        write_log(LOG_FILE, 'fin', None, None, None)
        print('servidor finalizado')
