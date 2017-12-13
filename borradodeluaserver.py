"""
class EchoHandler(socketserver.DatagramRequestHandler):
    """
  #  Echo server class
    """
    LISTA = ['INVITE', 'ACK', 'BYE']

    def error(self, line):
        """
       # method to verify if message is correct
        """
        fail = False
        try:
            if len(line) != 3:
                fail = True
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
        
       # handle method of the server class
        """
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            print(line.decode('utf-8'))
            if not line:
                break
            list_line_decode = line.decode('utf-8').split(' ')
            method = list_line_decode[0]
            if self.error(list_line_decode):
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            elif method == 'INVITE':
                self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n" +
                                 b"SIP/2.0 180 Ringing\r\n\r\n" +
                                 b"SIP/2.0 200 OK\r\n\r\n")
            elif method == 'ACK':
                a_ejecutar = './mp32rtp -i 127.0.0.1 -p 23032 < ' + AUDIO_FILE
                print('Vamos a ejecutar', a_ejecutar)
                os.system(a_ejecutar)
            elif method == 'BYE':
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            elif method not in self.LISTA:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit('Usage: python3 server.py IP port audio_file')
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    AUDIO_FILE = sys.argv[3]
    if not os.path.exists(AUDIO_FILE):
        sys.exit("Audio_file doesn't exists")
    # Creamos servidor de eco y escuchamos
    SERV = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')
"""
