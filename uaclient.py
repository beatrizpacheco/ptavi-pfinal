#!#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Class (and main program) of the uaclient
"""

import hashlib
import os
import socket
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class UAClientHandler(ContentHandler):
    """
    method to read configuration information of the config file
    """
    config = {}

    def __init__(self):
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
        return self.config

    def elparser(fich):
        parser = make_parser()
        ua_handler = UAClientHandler()
        parser.setContentHandler(ua_handler)
        parser.parse(open(fich))
        return ua_handler.get_tags()


def checking(nonce):
    """
    method to get the number result of hash function
    with password and nonce
    """
    function_check = hashlib.md5()
    function_check.update(bytes(str(nonce), "utf-8"))
    function_check.update(bytes(str(PASSWORD), "utf-8"))
    function_check.digest()
    return function_check.hexdigest()


def write_log(fichero, metodo, address, port, message):
    """
    method to write log
    """
    current_hour = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    fich = open(fichero, "a")
    if metodo == 'open':
        line = (current_hour + " Starting...")
    elif metodo == 'send':
        line = (current_hour + " Sent to " + address + ':' + str(port) + ': ' +
                message.replace('\r\n', ' '))
    elif metodo == 'receive':
        line = (current_hour + " Received from " + address + ':' + str(port) +
                ': ' + message.replace('\r\n', ' '))
    elif metodo == 'error':
        line = (current_hour + " Error: " + message.replace('\r\n', ' '))
    elif metodo == 'fin':
        line = (current_hour + " Finishing.")

    fich.write(line + '\r\n')
    fich.close()


if __name__ == "__main__":

    if len(sys.argv) != 4:
        sys.exit('Usage: python3 uaclient.py config method opcion')

    CONFIG = sys.argv[1]
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    METHOD = sys.argv[2]
    LISTA = ['REGISTER', 'INVITE', 'BYE']
    if METHOD not in LISTA:
        sys.exit('SIP/2.0 405 Method Not Allowed\r\n')
    OPCION = sys.argv[3]
    print(UAClientHandler.elparser(CONFIG))  # comprobacion, no haria falta

    # Doy valor a las variables segun la info del xml
    if UAClientHandler.config["regproxy_ip"] is None:
        IP_PROXY = "127.0.0.1"
    else:
        IP_PROXY = UAClientHandler.config['regproxy_ip']
    PORT_PROXY = int(UAClientHandler.config['regproxy_puerto'])
    USER = UAClientHandler.config['account_username']
    PASSWORD = UAClientHandler.config['account_passwd']
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    RTPAUDIO = UAClientHandler.config['rtpaudio_puerto']
    AUDIO_FILE = UAClientHandler.config['audio_path']
    LOG_FILE = UAClientHandler.config['log_path']

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    # del servidor regproxy
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY, PORT_PROXY))
        # write starting
        write_log(LOG_FILE, 'open', None, None, None)
        if METHOD == 'REGISTER':
            TO_SEND = (METHOD + ' sip:' + USER + ':' + str(PORT_UASERVER) +
                       ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n')
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            # write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, TO_SEND)

        elif METHOD == 'INVITE':
            TO_SEND = (METHOD + ' sip:' + OPCION +
                       ' SIP/2.0\r\nContent-Type: application/sdp' +
                       '\r\n\r\n' +
                       'v=0\r\n' +
                       'o=' + USER + ' ' + IP_UASERVER + '\r\n' +
                       's=misesion\r\n' +
                       't=0\r\n' +
                       'm=audio ' + RTPAUDIO + ' RTP\r\n')
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            # write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, TO_SEND)

        elif METHOD == 'BYE':
            TO_SEND = (METHOD + ' sip:' + OPCION + ' SIP/2.0\r\n')
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            # write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, TO_SEND)

        try:
            DATA = my_socket.recv(1024)
            print('Recibido -- ' + DATA.decode('utf-8'))
            MESSAGE_RECEIVE = DATA.decode('utf-8').split()

            if MESSAGE_RECEIVE:
                # write receive
                write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY,
                          DATA.decode('utf-8'))

            if MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '100':  # 100-180-200
                # cojo ip y puerto
                USER_RECEPTOR = MESSAGE_RECEIVE[12].split('=')[1]
                IP_RECEPTOR = MESSAGE_RECEIVE[13]
                PORT_RECEPTOR = MESSAGE_RECEIVE[17]
                # write receive
                write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY,
                          DATA.decode('utf-8'))
                # mando ack
                TO_SEND = ('ACK sip:' + USER_RECEPTOR + ' SIP/2.0\r\n')
                my_socket.send(bytes(TO_SEND, 'utf-8'))
                # write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, TO_SEND)
                # abro socket con el otro y mando rtp
                A_EJECUTAR = ('./mp32rtp -i ' + IP_RECEPTOR + ' -p ' +
                              PORT_RECEPTOR + ' < ' + AUDIO_FILE)
                print('Vamos a ejecutar', A_EJECUTAR)
                os.system(A_EJECUTAR)
                print('creo que ya se ha acabado')
                # write send
                write_log(LOG_FILE, 'send', IP_RECEPTOR, PORT_RECEPTOR,
                          ('Vamos a ejecutar' + A_EJECUTAR))

            elif MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '401':
                VALIDATION = MESSAGE_RECEIVE[5].split('=')[1][1:-1]
                RESPONSE = checking(VALIDATION)
                TO_SEND = ('REGISTER sip:' + USER + ':' +
                           str(PORT_UASERVER) + ' SIP/2.0\r\nExpires: ' +
                           OPCION + '\r\n' +
                           'Authorization: Digest response="' +
                           RESPONSE + '"\r\n\r\n')
                my_socket.send(bytes(TO_SEND, 'utf-8'))
                # write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, TO_SEND)
                # Espero recibir el 200ok
                my_socket.connect((IP_PROXY, PORT_PROXY))
                DATA = my_socket.recv(1024)
                print(DATA.decode('utf-8'))
                # write receive
                write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY,
                          DATA.decode('utf-8'))

            elif MESSAGE_RECEIVE and ((MESSAGE_RECEIVE[1] == '400') or
                                      (MESSAGE_RECEIVE[1] == '404') or
                                      (MESSAGE_RECEIVE[1] == '405')):
                print(DATA.decode('utf-8'))
                # write error
                write_log(LOG_FILE, 'error', None, None,
                          DATA.decode('utf-8'))

            print("Terminando socket...")

        except ConnectionRefusedError:
            # write error
            TO_SEND = ("Error: no server listening at " + IP_PROXY +
                       " port " + str(PORT_PROXY))
            write_log(LOG_FILE, 'error', None, None, TO_SEND)
            exit(TO_SEND)

    print("Fin.")
    # write fin
    write_log(LOG_FILE, 'fin', None, None, None)
