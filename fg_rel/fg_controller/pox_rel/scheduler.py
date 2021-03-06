import json, pprint, os, inspect, sys, logging
from xmlparser import XMLParser
from graphman import GraphMan
from scheduling_optimization import SchingOptimizer
from perf_plot import PerfPlotter
from control_comm_intf import check_msg,ControlCommIntf

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"ext")))
if cmd_subfolder not in sys.path:
   sys.path.insert(0, cmd_subfolder)
# to import pox modules while __name__ == "__main__"
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parentdir not in sys.path:
  sys.path.insert(0,parentdir)
  
from pox.lib.revent.revent import Event, EventMixin
class SendMsgToUser(Event):
  def __init__ (self, msg=None, info_dict=None):
    Event.__init__(self)
    self.msg = msg
    self.info_dict = info_dict
  @property
  def get_msg(self):
    return self.msg
  @property
  def get_info_dict(self):
    return self.info_dict
  
class EventChief(EventMixin):
  _eventMixin_events = set([
    SendMsgToUser,
  ])
  def raise_event(self, event_type, arg1, arg2):
    if event_type == 'send_msg_to_user':
      #sargs = ["Generic"] #[sch_res, "Generic"]
      self.raiseEvent(SendMsgToUser(arg1, arg2)) #sch_res
    elif event_type == 'sth_else':
      pass
    else:
      print 'Unknown event_type: ', event_type
      raise KeyError('Unknown event_type')
#
info_dict = {'acterl_addr':('127.0.0.1',7999), #192.168.56.1
             'lacter_addr':('127.0.0.1',7998),
             'scher_vip':'10.0.0.255',
             'base_sport':6000,
             'sching_port':7000
            }
  
class Scheduler(object):
  event_chief = EventChief()
  def __init__(self, xml_net_num, sching_logto):
    logging.basicConfig(level=logging.DEBUG)
    self.sching_logto = sching_logto
    if is_scheduler_run:
      self.xml_parser = XMLParser("net_2p_stwithsingleitr.xml", str(xml_net_num))
    else:
      self.xml_parser = XMLParser("ext/net_2p_stwithsingleitr.xml", str(xml_net_num))
    self.gm = GraphMan()
    self.init_network_from_xml()
    #Useful state variables
    self.last_sching_id_given = -1
    self.last_sch_req_id_given = -1
    self.last_tp_dst_given = info_dict['base_sport']-1
    #Scher state dicts
    self.num_dstusers = 0
    self.users_beingserved_dict = {} #user_ip:{'gw_dpid':<>,'gw_conn_port':<> ...}
    #
    self.N = 0 #num_activesessions
    self.alloc_dict = None
    self.sessions_beingserved_dict = {}
    self.sessions_pre_served_dict = {}
    self.sid_res_dict = {}
    self.actual_res_dict = self.gm.give_actual_resource_dict()
    #for perf plotting
    self.perf_plotter = PerfPlotter(self.actual_res_dict)
    #for control_comm
    self.cci = ControlCommIntf()
    self.cci.reg_commpair(sctag = 'scher-acter',
                          proto = 'tcp',
                          _recv_callback = self._handle_recvfromacter,
                          s_addr = info_dict['lacter_addr'],
                          c_addr = info_dict['acterl_addr'] )
  #########################  _handle_*** methods  #######################
  def _handle_recvfromacter(self, msg):
    #msg = [type_, data_]
    [type_, data_] = msg
    if type_ == 'sp_sching_reply':
      s_id, p_id = int(data_['s_id']), int(data_['p_id'])
      reply = data_['reply']
      if reply == 'done':
        #updating global dicts
        self.sessions_beingserved_dict[s_id]['sching_job_done'][p_id] = True
        #get s_alloc_info
        s_alloc_info = self.alloc_dict['s-wise'][s_id]
        s_pl = s_alloc_info['parism_level']
        #get s_info, dtsuserinfo
        s_info = self.sessions_beingserved_dict[s_id]
        p_ip = s_info['p_c_ip_list'][0]
        user_info = self.users_beingserved_dict[p_ip]
        info_dict = {'ip': p_ip,
                     'mac': user_info['mac'],
                     'gw_dpid': user_info['gw_dpid'],
                     'gw_conn_port': user_info['gw_conn_port'] }
        msg = json.dumps({'type':'sching_reply',
                          'data':{'parism_level':s_pl,
                                  'p_bw':s_alloc_info['p_bw'][0:s_pl],
                                  'p_tp_dst':s_info['tp_dst_list'][0:s_pl] } })
        #fire send_sching_reply to the user
        Scheduler.event_chief.raise_event('send_msg_to_user',msg,info_dict)
      else:
        logging.error('Unexpected reply=%s', reply)
  
  def _handle_recvfromdtsuser(self, msg, dtsuserinfo_dict):
    msg_ = check_msg('recv', 'dts-user', msg)
    if msg_ == None:
      print 'msg is not proto-good'
      return
    #msg_ = [type_, data_]
    [type_, data_] = msg_
    #
    src_ip = dtsuserinfo_dict['src_ip']
    src_mac = dtsuserinfo_dict['src_mac']
    src_gw_dpid = dtsuserinfo_dict['src_gw_dpid']
    src_gw_conn_port = dtsuserinfo_dict['src_gw_conn_port']
    info_dict = {'ip': src_ip,
                 'mac': src_mac,
                 'gw_dpid': src_gw_dpid,
                 'gw_conn_port': src_gw_conn_port}
    if type_ == 'join_req':
      if self.welcome_user(user_ip = src_ip,
                           user_mac = src_mac,
                           gw_dpid = src_gw_dpid,
                           gw_conn_port = src_gw_conn_port ):
        msg = json.dumps({'type':'join_reply',
                          'data':'welcome' })
        Scheduler.event_chief.raise_event('send_msg_to_user',msg,info_dict)
      else: #fire send_neg_reply to the user
        msg = json.dumps({'type':'join_reply',
                          'data':'sorry' })
        Scheduler.event_chief.raise_event('send_msg_to_user',msg,info_dict)
    elif type_ == 'sching_req':
      if self.welcome_session(p_c_ip_list = [src_ip, data_['c_ip']],
                              req_dict = data_['req_dict'],
                              app_pref_dict = data_['app_pref_dict'] ):
        #TODO: for now ...
        self.do_sching()
      else: #fire send_neg_reply to the user
        msg = json.dumps({'type':'sching_reply',
                          'data':'sorry' })
        Scheduler.event_chief.raise_event('send_msg_to_user',msg,info_dict)
  ####################  scher_state_management  methods  #######################
  def print_scher_state(self):
    print '<---------------------------------------->'
    print 'is_scheduler_run: ', is_scheduler_run
    print 'users_beingserved_dict:'
    pprint.pprint(self.users_beingserved_dict)
    print 'sessions_beingserved_dict:'
    pprint.pprint(self.sessions_beingserved_dict)
    print 'sessions_pre_served_dict:'
    pprint.pprint(self.sessions_pre_served_dict)
    print '<---------------------------------------->'
  
  def next_sching_id(self):
    self.last_sching_id_given += 1
    return  self.last_sching_id_given
  
  def next_sch_req_id(self):
    self.last_sch_req_id_given += 1
    return  self.last_sch_req_id_given
  
  def next_tp_dst(self):
    self.last_tp_dst_given += 1
    return  self.last_tp_dst_given
  
  def did_user_joindts(self, user_ip):
    return user_ip in self.users_beingserved_dict
  
  def welcome_user(self, user_ip, user_mac, gw_dpid, gw_conn_port):
    if self.did_user_joindts(user_ip):
      print 'user_ip=%s already joined' % user_ip
      return False
    #
    self.users_beingserved_dict.update({user_ip:{'gw_dpid':gw_dpid,
                                                 'gw_conn_port':gw_conn_port,
                                                 'mac': user_mac } })
    print 'welcome user: ip=%s, mac=%s, gw_dpid=%s, gw_conn_port=%s' % (user_ip,user_mac,gw_dpid,gw_conn_port)
    return True
  
  #not used now, for future
  def bye_user(self, user_ip):
    if not self.did_user_joindts(user_ip):
      print 'user_ip=%s is not joined' % user_ip
      return False
    #
    del self.users_beingserved_dict[user_ip]
    print 'bye user: ip=%s' % user_ip
    return True
  
  def welcome_session(self, p_c_ip_list, req_dict, app_pref_dict):
    ''' sch_req_id: should be unique for every sch_session '''
    [p_ip, c_ip] = p_c_ip_list
    if not (self.did_user_joindts(p_ip) and self.did_user_joindts(c_ip)):
      print 'nonjoined user in sching_req'
      return False
    #
    p_c_gwtag_list = ['s'+str(self.users_beingserved_dict[p_ip]['gw_dpid']),
                      's'+str(self.users_beingserved_dict[c_ip]['gw_dpid']) ]
    #update global var, list and dicts
    self.N += 1
    s_pl = req_dict['parism_level']
    s_tp_dst_list = [self.next_tp_dst() for i in range(0,s_pl)]
    sch_req_id = self.next_sch_req_id()
    self.sessions_beingserved_dict.update(
      {sch_req_id:{'tp_dst_list': s_tp_dst_list,
                   'p_c_ip_list': p_c_ip_list,
                   'p_c_gwtag_list': p_c_gwtag_list,
                   'app_pref_dict': app_pref_dict,
                   'req_dict': req_dict,
                   'sching_job_done':[False]*s_pl }
      }
    )
    #print 'self.sessions_beingserved_dict: '
    #pprint.pprint(self.sessions_beingserved_dict)
    #
    return True
  
  def bye_session(self, sch_req_id):
    self.N -= 1
    # Send sessions whose "sching job" is done is sent to pre_served category
    self.sessions_pre_served_dict.update(
    {sch_req_id: self.sessions_beingserved_dict[sch_req_id]})
    del self.sessions_beingserved_dict[sch_req_id]
  
  def init_network_from_xml(self):
    node_edge_lst = self.xml_parser.give_node_and_edge_list_from_xml()
    #print 'node_lst:'
    #pprint.pprint(node_edge_lst['node_lst'])
    #print 'edge_lst:'
    #pprint.pprint(node_edge_lst['edge_lst'])
    self.gm.graph_add_nodes(node_edge_lst['node_lst'])
    self.gm.graph_add_edges(node_edge_lst['edge_lst'])
  #########################  sching_rel methods  ###############################
  def update_sid_res_dict(self):
    """
    Network resources will be only the ones on the session_shortest path.
    It resources need to lie on the session_shortest path.
    """
    logging.info('update_sid_res_dict:')
    #TODO: sessions whose resources are already specified no need for putting them in the loop
    for s_id in self.sessions_beingserved_dict:
      p_c_gwdpid_list = self.sessions_beingserved_dict[s_id]['p_c_gwtag_list']
      s_all_paths = self.gm.give_all_paths(p_c_gwdpid_list[0], p_c_gwdpid_list[1])
      #print out all_paths for debugging
      dict_ = {i:p for i,p in enumerate(s_all_paths)}
      logging.info('s_id=%s, all_paths=\n%s', s_id, pprint.pformat(dict_))
      #
      for i,p in dict_.items():
        p_net_edge_list = self.gm.pathlist_to_netedgelist(p)
        p_itres_list = self.gm.give_itreslist_on_path(p)
        if not (s_id in self.sid_res_dict):
          self.sid_res_dict[s_id] = {'s_info':{}, 'ps_info':{}}
        self.sid_res_dict[s_id]['ps_info'].update(
          {i: {'path': p,
               'net_edge_list': p_net_edge_list,
               'itres_list': p_itres_list
              }
          })
  
  def do_sching(self):
    '''
    Currently for active sessions, gets things together to work sching logic and
    then sends corresponding walk/itjob rules to correspoding actuator - which is
    a single actuator right now !
    '''
    sching_id = self.next_sching_id()
    if self.sching_logto == 'file':
      fname = 'ext/sching_decs/sching_'+sching_id+'.log'
      logging.basicConfig(filename=fname,filemode='w',level=logging.DEBUG)
    elif self.sching_logto == 'console':
      logging.basicConfig(level=logging.DEBUG)
    else:
      logging.error('Unexpected sching_logto=%s', self.sching_logto)
      return
    #
    logging.info('<<< sching_id=%s starts >>>', sching_id)
    self.update_sid_res_dict()
    sching_opter = SchingOptimizer(self.sessions_beingserved_dict,
                                   self.actual_res_dict,
                                   self.sid_res_dict )
    sching_opter.solve()
    self.alloc_dict = sching_opter.get_sching_result()
    logging.info('alloc_dict=\n%s', pprint.pformat(self.alloc_dict))
    #
    """
    logging.info('saving sching_dec to figs...')
    self.perf_plotter.save_sching_result(g_info_dict = self.alloc_dict['general'],
                                         s_info_dict = self.alloc_dict['s-wise'],
                                         res_info_dict = self.alloc_dict['res-wise'])
    """
    #Convert sching decs to rules
    for s_id in range(0,self.N):
      s_allocinfo_dict = self.alloc_dict['s-wise'][s_id]
      #
      itwalkinfo_dict = s_allocinfo_dict['itwalkinfo_dict']
      p_walk_dict = s_allocinfo_dict['pwalk_dict']
      for p_id in range(0,s_allocinfo_dict['parism_level']):
        p_walk = p_walk_dict[p_id]
        sp_walk__tprrule = \
          self.get_spwalkrule__sptprrule(s_id, p_id,
                                         p_walk = p_walk,
                                         pitwalkbundle_dict = itwalkinfo_dict[p_id])
        logging.info('for s_id=%s, p_id=%s;', s_id, p_id)
        #print 'walkrule:'
        #pprint.pprint(sp_walk__tprrule['walk_rule'])
        #print 'itjob_rule:'
        #pprint.pprint(sp_walk__tprrule['itjob_rule'])
        #
        #Dispatching rule to actuator_actuator
        msg = json.dumps({'type':'sp_sching_dec',
                          'data':{'s_id':s_id, 'p_id':p_id,
                                  'walk_rule':sp_walk__tprrule['walk_rule'],
                                  'itjob_rule':sp_walk__tprrule['itjob_rule']} })
        self.cci.send_to_client('scher-acter', msg)
    logging.info('<<< sching_id=%s ends >>>', sching_id)
  
  def get_spwalkrule__sptprrule(self,s_id,p_id,p_walk,pitwalkbundle_dict):
    def get_swportname(dpid, port):
      return 's'+str(dpid)+'-eth'+str(port)
    #print '---> for s_id:%i' % s_id
    #print 'pitwalkbundle_dict:'
    #pprint.pprint(pitwalkbundle_dict)
    #print 'p_walk: ', p_walk
    s_info_dict =  self.sessions_beingserved_dict[s_id]
    s_tp_dst = s_info_dict['tp_dst_list'][p_id]
    p_c_ip_list = s_info_dict['p_c_ip_list']
    #
    itjob_rule_dict = {}
    #
    walk_rule = []
    cur_from_ip = p_c_ip_list[0]
    cur_to_ip = p_c_ip_list[1]
    duration = 50
    cur_node_str = None
    for i,node_str in list(enumerate(p_walk)):#node = next_hop
      if i == 0:
        cur_node_str = node_str
        #for adding reverse-walk rule for p_gw_sw
        user_info_dict = self.users_beingserved_dict[cur_from_ip]
        swportname = get_swportname(dpid = user_info_dict['gw_dpid'],
                                    port = user_info_dict['gw_conn_port'])
        node = self.gm.get_node(node_str)
        walk_rule.append({'conn':[node['dpid'],cur_to_ip],
                          'typ':'forward',
                          'wc':[cur_to_ip,p_c_ip_list[0],int(s_tp_dst)],
                          'rule':[swportname, duration] })
        #
        continue
      cur_node = self.gm.get_node(cur_node_str)
      if cur_node['type'] == 't':
        cur_node_str = node_str
        continue
      #
      node = self.gm.get_node(node_str)
      edge = self.gm.get_edge(cur_node_str, node_str)
      if node['type'] == 't': #sw-t
        walk_rule.append({'conn':[cur_node['dpid'],cur_from_ip],
                          'typ':'modify_forward',
                          'wc':[cur_from_ip,cur_to_ip,int(s_tp_dst)],
                          'rule':[node['ip'],node['mac'],edge['pre_dev'],duration]
                         })
        if not (cur_node['dpid'] in itjob_rule_dict):
          itjob_rule_dict[cur_node['dpid']] = [{
            'tpr_ip':node['ip'],
            'tpr_mac':node['mac'],
            'swdev_to_tpr':edge['pre_dev'],
            'assigned_job': pitwalkbundle_dict['itbundle'][node_str],
            'session_tp': int(s_tp_dst),
            'consumer_ip': cur_to_ip,
            'datasize': pitwalkbundle_dict['p_info']['datasize'] }]
        else:
          itjob_rule_dict[cur_node['dpid']].append( [{
            'tpr_ip':node['ip'],
            'tpr_mac':node['mac'],
            'swdev_to_tpr':edge['pre_dev'],
            'assigned_job':pitwalkbundle_dict['itbundle'][node_str],
            'session_tp': int(s_tp_dst),
            'consumer_ip': cur_to_ip,
            'datasize': pitwalkbundle_dict['p_info']['datasize'] }] )
        cur_from_ip = node['ip']
      elif node['type'] == 'sw': #sw-sw
        walk_rule.append({'conn':[cur_node['dpid'],cur_from_ip],
                          'typ':'forward',
                          'wc':[cur_from_ip,cur_to_ip,int(s_tp_dst)],
                          'rule':[edge['pre_dev'], duration] })
        cur_from_ip
        #for reverse walk: data from c to p
        walk_rule.append({'conn':[node['dpid'],cur_to_ip],
                          'typ':'forward',
                          'wc':[cur_to_ip,p_c_ip_list[0],int(s_tp_dst)],
                          'rule':[edge['post_dev'], duration] })
        '''
        #to deliver sch_response to src
        walk_rule.append({'conn':[node['dpid'],info_dict['scher_vip']],
                          'typ':'forward',
                          'wc':[info_dict['scher_vip'],p_c_ip_list[0], info_dict['sching_port']],
                          'rule':[edge['post_dev'], duration] })
        '''
      else:
        raise KeyError('Unknown node_type')
      cur_node_str = node_str
    #default rule to forward packet to consumer
    user_info_dict = self.users_beingserved_dict[cur_to_ip]
    swportname = get_swportname(dpid = user_info_dict['gw_dpid'],
                                port = user_info_dict['gw_conn_port'])
    walk_rule.append({'conn':[user_info_dict['gw_dpid'],cur_from_ip],
                      'typ':'forward',
                      'wc':[cur_from_ip,cur_to_ip,int(s_tp_dst)],
                      'rule':[swportname,duration] })
    """
    #default rule to forward sch_response to producer
    walk_rule.append({'conn':[11,info_dict['scher_vip']],
                      'typ':'forward',
                      'wc':[info_dict['scher_vip'],p_c_ip_list[0]],
                      'rule':['s11-eth1',duration] })
    """
    return {'walk_rule':walk_rule, 'itjob_rule':itjob_rule_dict}
  
  ##############################################################################
  def test(self):
    userinfo_list = [ {'user_ip':'10.0.0.2','user_mac':'00:00:00:01:00:02','gw_dpid':11,'gw_conn_port':1},
                      {'user_ip':'10.0.0.1','user_mac':'00:00:00:01:00:01','gw_dpid':12,'gw_conn_port':2} ]
    for userinfo in userinfo_list:
      self.welcome_user(user_ip = userinfo['user_ip'],
                        user_mac = userinfo['user_mac'],
                        gw_dpid = userinfo['gw_dpid'],
                        gw_conn_port = userinfo['gw_conn_port'] )
    #
    num_session = 1
    req_dict_list = [ {'data_size':4, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':1, 'par_share':[1]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                      {'data_size':1, 'slack_metric':24, 'func_list':['f1','f2','f3'], 'parism_level':2, 'par_share':[0.5, 0.5]},
                    ]
    app_pref_dict_list = [
                          {'m_p': 10,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 10,'m_u': 0.5,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 0.5,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                          {'m_p': 1,'m_u': 1,'x_p': 0,'x_u': 0},
                         ]
    p_c_ip_list_list = [
                        ['10.0.0.2','10.0.0.1'],
                       ]
    for i in range(0, num_session):
      self.welcome_session(p_c_ip_list = p_c_ip_list_list[0],
                           req_dict = req_dict_list[i],
                           app_pref_dict = app_pref_dict_list[i] )
    self.do_sching()
  
is_scheduler_run = False
def main():
  global is_scheduler_run
  is_scheduler_run = True
  sch = Scheduler(xml_net_num = 1,
                  sching_logto = 'console')
  sch.test()
  #
  raw_input('Enter')
  #server.shutdown()


if __name__ == "__main__":
  main()
  
