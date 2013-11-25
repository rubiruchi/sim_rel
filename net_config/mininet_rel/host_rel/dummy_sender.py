#!/usr/bin/python

import sys,socket,json,getopt
import pprint

class DummySender(object):
  def __init__(self, dst_ip, dst_lport, proto):
    self.dst_ip = dst_ip
    self.dst_lport = dst_lport
    self.proto = proto
    self.sock = None
    #
    if self.proto == 'tcp':
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.connect((self.dst_ip, self.dst_lport))
    elif self.proto == 'udp':
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:
      print 'Unknown proto=%s.', self.proto
      sys.exit(2)
  
  def dummy_send(self, data_json):
    data = json.dumps(data_json)
    if self.proto == 'tcp':
      self.sock.sendall(data)
    elif self.proto == 'udp':
      self.sock.sendto(data, (self.dst_ip, self.dst_lport))
    #
    print 'proto:{}, sentto ip:{}, port:{}\ndata:{}'.format(self.proto, self.dst_ip, self.dst_lport, data)
  
  def test(self):
    if self.dst_lport == 7000: #send sching msgs
      data_json = {'type': 'sp_sching_reply',
                   'data': 'OK'}
      """
      data_json = {'type': 'sp_sching_reply',
                   'data': 'OK'}
      """
      """
      data_json = {'type': 'itjobrule',
                   'data': {'comp': 2.83333333313,
                            'data_to_ip': u'10.0.0.1',
                            'itfunc_dict': {u'f2': 2.83333333313},
                            'proc': 288.935318788,
                            's_tp': 6000,
                            'datasize': 0.5} }
      """
      self.dummy_send(data_json)
    elif self.dst_lport == 7998: #send to scher
      data_json = {'type': 'sp_sching_reply',
                   'data': 'OK'}
      self.dummy_send(data_json)
    else: #send dummy_session_data
      dummy_data = ''
      for i in range(0, 2):
        dummy_data += 'dummydata dummydata '
      self.dummy_send(dummy_data)
  
def main(argv):
  dst_ip = dst_lport = proto = None
  try:
    opts, args = getopt.getopt(argv,'',['dst_ip=','dst_lport=','proto='])
  except getopt.GetoptError:
    print 'dummy_sender.py --dst_ip=<> --dst_lport=<> --proto=tcp/udp'
    sys.exit(2)
  #Initializing variables with comman line options
  for opt, arg in opts:
    if opt == '--dst_ip':
       dst_ip = arg
    elif opt == '--dst_lport':
       dst_lport = int(arg)
    elif opt == '--proto':
       proto = arg
  #
  print 'dst_ip=%s, dst_lport=%s, proto=%s' % (dst_ip, dst_lport, proto)
  ds = DummySender(dst_ip, dst_lport, proto)
  ds.test()
  #
  raw_input('Enter')
  
if __name__ == "__main__":
  main(sys.argv[1:])
  
