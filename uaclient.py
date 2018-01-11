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

def checking(nonce):
    """
    method to get the number result of hash function
    with password and nonce
    """
    function_check = hashlib.md5()
    function_check.update(bytes(str(nonce), "utf-8"))#NO SE SI EL NONCE HAY QUE PASARLO A STRING O NO
    print('EL PUTO NONCE ES : "' + str(nonce) + '"') #COMPROBACION
    function_check.update(bytes(str(PASSWORD), "utf-8"))
    print('LA CONTRASEÑA ES : "' + str(PASSWORD) + '"') #COMPROBACION
    function_check.digest() #no sé si esto hace falta o directamente hex
    print('RESPONSE CLIENT: ' + function_check.hexdigest()) #COMPROBACION
    return function_check.hexdigest()

def write_log(fichero, metodo, ip, port, message):
    """
    method to write log
    """
    current_hour = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    fich = open(fichero, "a")
    if metodo == 'open':
        line = (current_hour + " Starting...")
    elif metodo == 'send':
        line = (current_hour + " Sent to " + ip + ':' + str(port) + ': ' + message.replace('\r\n',' '))
    elif metodo == 'receive':
        line = (current_hour + " Received from " + ip + ':' + str(port) + ': ' + message.replace('\r\n',' '))
    elif metodo == 'error':
        line = (current_hour + " Error: " + message.replace('\r\n',' '))
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
    LISTA = ['REGISTER', 'register', 'INVITE', 'invite', 'BYE', 'bye']
    if METHOD not in LISTA:
        sys.exit('SIP/2.0 405 Method Not Allowed\r\n' +
                 'Usage: python3 uaclient.py config method opcion')
    OPCION = sys.argv[3]
    print(UAClientHandler.elparser(CONFIG))
    
    #Doy valor a las variables segun la info del xml
    if UAClientHandler.config["regproxy_ip"] == None:
        IP_PROXY = "127.0.0.1"
    else:
        IP_PROXY = UAClientHandler.config['regproxy_ip']
    PORT_PROXY = int(UAClientHandler.config['regproxy_puerto'])
    USER = UAClientHandler.config['account_username']
    PASSWORD = UAClientHandler.config['account_passwd']
    IP_UASERVER = UAClientHandler.config['uaserver_ip']
    PORT_UASERVER = int(UAClientHandler.config['uaserver_puerto'])
    RTPAUDIO = UAClientHandler.config['rtpaudio_puerto']
    print('EL PUERTO DONDE ESPERO RECIBIR RTP EEEEEEEEEEEEEEEEES: ' + RTPAUDIO)
    AUDIO_FILE = UAClientHandler.config['audio_path']
    LOG_FILE = UAClientHandler.config['log_path']
   
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto 
    # del servidor regproxy
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY, PORT_PROXY))
        #write starting
        write_log(LOG_FILE, 'open', None, None, None)
        if (METHOD == 'REGISTER' or METHOD == 'register'):
            to_send = (METHOD + ' sip:' + USER + ':' + str(PORT_UASERVER) + 
                       ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n')
            my_socket.send(bytes(to_send, 'utf-8') + b'\r\n')
            print(METHOD + ' sip:' + USER + ':' + str(PORT_UASERVER) + 
                  ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n') #COMPROBACION
            #write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)
        
        elif (METHOD == 'INVITE' or METHOD == 'invite'):
            to_send = (METHOD + ' sip:' + OPCION  +
                       ' SIP/2.0\r\nContent-Type: application/sdp' + 
                       '\r\n\r\n' + 
                       'v=0\r\n' + 
                       'o=' + USER + ' ' + IP_UASERVER + '\r\n' +
                       's=misesion\r\n' +
                       't=0\r\n' +
                       'm=audio ' + RTPAUDIO + ' RTP\r\n')
            my_socket.send(bytes(to_send, 'utf-8') + b'\r\n')
            #write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)

        elif (METHOD == 'BYE' or METHOD == 'bye'):
            to_send = (METHOD + ' sip:' + OPCION  + ' SIP/2.0\r\n')
            my_socket.send(bytes(to_send, 'utf-8') + b'\r\n')
            #write send
            write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)

        try:
            DATA = my_socket.recv(1024)
            print('Recibido -- ' + DATA.decode('utf-8'))
            MESSAGE_RECEIVE = DATA.decode('utf-8').split()
            print('UEEEEEEEEEEEEEEEEEEEEEE: ' + DATA.decode('utf-8'))
            
            if MESSAGE_RECEIVE:
                #write receive
                write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY, DATA.decode('utf-8'))
            
            """
            if MESSAGE_RECEIVE[0] == 'INVITE':
                #CREO QUE EN EL UACLIENT NO ME HACE FALTA INVITE
                #cojo el origen, ip y puerto
                print('MESSAGE_RECEIVE eeeeeees: ' + DATA.decode('utf-8'))
                user_emisor = MESSAGE_RECEIVE[6].split('=')[1]
                ip_emisor = MESSAGE_RECEIVE[7]
                port_emisor = MESSAGE_RECEIVE[11]
                #mando 100, 180, 200 con mi sdp
                my_socket.send(bytes("SIP/2.0 100 Trying\r\n\r\n" +
                                     "SIP/2.0 180 Ringing\r\n\r\n" +
                                     "SIP/2.0 200 OK\r\n\r\n" +
                                     '\r\n\r\n' + 
                                     'v=0\r\n' + 
                                     'o=' + USER + ' ' + IP_UASERVER + '\r\n' +
                                     's=misesion' + '\r\n' +
                                     't=0\r\n' +
                                     'm=audio ' + RTPAUDIO + ' RTP\r\n', 'utf-8'))
                my_socket.connect((IP_PROXY, PORT_PROXY))
                DATA = my_socket.recv(1024)
                #si es ack pues abro rtp
                MESSAGE_RECEIVE = DATA.decode('utf-8').split()
                if MESSAGE_RECEIVE[0] == 'ACK' or MESSAGE_RECEIVE[0] == 'ack':
                    print('de PUUUUUUUTA madre, me llega el ack')
                    print(DATA.decode('utf-8'))
                    #envio rtp
                    """"""
                    #my_socket.connect((ip_emisor, port_emisor))
                    """"""
                    a_ejecutar = './mp32rtp -i ' + ip_emisor + ' -p ' + port_emisor + ' < ' + AUDIO_FILE
                    print('Vamos a ejecutar', a_ejecutar)
                    os.system(a_ejecutar)
                    print('creo que ya se ha acabado')
            """        
            if MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '100':  #100-180-200
                #cojo ip y puerto
                user_receptor = MESSAGE_RECEIVE[12].split('=')[1]
                ip_receptor = MESSAGE_RECEIVE[13]
                port_receptor = MESSAGE_RECEIVE[17]
                #write receive
                #write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY, DATA.decode('utf-8'))
                #mando ack
                to_send = ('ACK sip:' + user_receptor + ' SIP/2.0\r\n')
                my_socket.send(bytes(to_send, 'utf-8'))
                #write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)
                #abro socket con el otro y mando rtp
                a_ejecutar = './mp32rtp -i ' + ip_receptor + ' -p ' + port_receptor + ' < ' + AUDIO_FILE
                print('Vamos a ejecutar', a_ejecutar)
                os.system(a_ejecutar)
                print('creo que ya se ha acabado')
                #write send
                write_log(LOG_FILE, 'send', ip_receptor, port_receptor, ('Vamos a ejecutar' + a_ejecutar))

            elif MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '400':
                print(DATA.decode('utf-8'))
                
            
            elif MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '401':
                nonce = MESSAGE_RECEIVE[5].split('=')[1][1:-1]
                print('EL PUTO NONCE de abajo ES : ' + str(nonce)) #COMPROBACION
                response = checking(nonce)
                to_send = (METHOD + ' sip:' + USER + ':' +
                           str(PORT_UASERVER) + ' SIP/2.0\r\nExpires: ' +
                           OPCION + '\r\n' + 
                           'Authorization: Digest response="' + 
                           response + '"\r\n\r\n')
                my_socket.send(bytes(to_send, 'utf-8'))
                #write send
                write_log(LOG_FILE, 'send', IP_PROXY, PORT_PROXY, to_send)
                #Espero recibir el 200ok
                print('AHORA DEBERIA DE RECIBIR EL 200OK') #COMPROBACION
                my_socket.connect((IP_PROXY, PORT_PROXY))
                DATA = my_socket.recv(1024)
                print(DATA.decode('utf-8'))
                #write receive
                write_log(LOG_FILE, 'receive', IP_PROXY, PORT_PROXY, DATA.decode('utf-8'))
            
            elif MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '404':
                print(DATA.decode('utf-8'))
            
            elif MESSAGE_RECEIVE and MESSAGE_RECEIVE[1] == '405':
                print(DATA.decode('utf-8'))
            
            #else diciendo que ha habido algun error?
            print("Terminando socket...")
            
        except ConnectionRefusedError:
            #write error
            to_send = ("Error: no server listening at " + IP_PROXY + 
                       " port " + str(PORT_PROXY))
            write_log(LOG_FILE, 'error', None, None, to_send)
            exit(to_send)
            
    print("Fin.")
    #write fin
    write_log(LOG_FILE, 'fin', None, None, None)
    
