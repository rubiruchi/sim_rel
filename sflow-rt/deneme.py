import socket, sys

class SchSocket(object):
  
  def __init__(self, s_ip, s_port):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s_ip = s_ip
    self.s_port = s_port

  def send(self, msg):
    totalsent = 0
    msg_len = len(msg)
    while totalsent < msg_len:
      sent = self.sock.send(msg[totalsent:])
      if sent == 0:
        raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

  def receive(self):
    msg = ''
    msg_len = len(msg)
    while len(msg) < msg_len:
        chunk = self.sock.recv(msg_len-len(msg))
        if chunk == '':
            raise RuntimeError("socket connection broken")
        msg = msg + chunk
    return msg

class SchClient(SchSocket):
  def __init__(self, *args, **kwargs):
    super(SchClient, self).__init__(*args, **kwargs)
    self.sock.connect((self.s_ip, int(self.s_port)))

class SchServer(SchSocket):
  def __init__(self, *args, **kwargs):
    super(SchServer, self).__init__(*args, **kwargs)
    self.sock.bind((self.s_ip, int(self.s_port)))
    self.listen()

  def listen(self):
    print "SchServer is listening from s_ip: ", self.s_ip, " s_port: ", self.s_port
    self.sock.listen(5)
    while True:
      c, addr = self.sock.accept()
      print 'Got connection from', addr
      c.recv()
      #c.send('Thank you for connecting')
      #c.close()

def main():
  if len(sys.argv) != 4:
    raise RuntimeError('argv = [type, s_addr, s_port]')
  
  if sys.argv[1] == 's':
    #print 'socket.gethostbyname(socket.gethostname(): ', socket.gethostbyname(socket.gethostname())
    s = SchServer(socket.gethostbyname(socket.gethostname()), 9999)
  elif sys.argv[1] == 'c':
    c = SchClient(sys.argv[2], sys.argv[3])
    c.send('SOS')

  #c.send('SOS')
  
if __name__ == "__main__":
  main()


