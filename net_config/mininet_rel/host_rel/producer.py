import SocketServer as SS
import sys,socket,json
import pprint

class Producer(object):
  def __init__(self, c_addr, c_lport, fname):
    self.fname = fname
    self.c_addr = c_addr
    self.c_lport = c_lport
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  def send_sch_request(self, sch_req):
    data = json.dumps(sch_req)
    self.sock.sendto(data, (self.c_addr, self.c_lport))
    print 'sentto addr:{}, port:{}\ndata:{}'.format(self.c_addr, self.c_lport, data)

  def test(self):
    sch_req = {'req_dict': {'data_amount': 1, 'slack_metric': 24, 'func_list': ['f1', 'f2', 'f3']},
               'app_pref_dict': {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0}
              }
    self.send_sch_request(sch_req)
  
def main():
  if len(sys.argv) != 4:
    raise RuntimeError('argv = [c_addr, c_lport, fname]')
  c_addr = sys.argv[1]
  c_lport = int(sys.argv[2])
  fname = sys.argv[3]
  #
  p = Producer(c_addr, c_lport, fname)
  p.test()
  #
  raw_input('Enter')
  
  
  
if __name__ == "__main__":
  main()