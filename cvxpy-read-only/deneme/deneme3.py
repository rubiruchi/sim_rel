from cvxpy import *

def main():
  N = 2
  D = [1, 0.1] #Mb
  L = [2, 2]  #ms
  num_f = [3, 1]
  slack = [24, 4]
  #
  tt = variable(N,1, name = 'tt')
  #
  bw = variable(N,1, name = 'bw') #Mbps
  proc = variable(N,1, name = 'proc') #Mflop/s
  dur = variable(N,1, name = 'dur') #ms
  n = variable(N,1, name = 'n')
  # dummy opt vars
  d1 = variable(3,1, name='d1')
  # F0
  h_F0 = parameter(N,1, name = 'h_F0')
  for i in range(0,N):
    h_F0[i,0] = square(tt[i,0]-slack[i])
  F0 = max(h_F0)
  # F1
  h_F1 = parameter(N,1, name = 'h_F1')
  for i in range(0,N):
    h_F1[i,0] = n[i,0]*(num_f[i]**-1)
  F1 = min(h_F1)
  # F = F0 - scal_var*F1
  scal_var = 2
  F = F0 - scal_var*F1
  # for n <= num_funcs
  num_f_vec = matrix(num_f).T
  # trans_time <= tt
  trans_t = variable(N,1, name = 'trans_t')
  for i in range(0,N):
    trans_t[i, 0] = 1000*D[i]*quad_over_lin(1, bw[i,0])+L[i]+ \
                    1000*D[i]*quad_over_lin(n[i,0], proc[i,0])+ \
                    dur[i,0]

  prog = program(minimize(F),
                  [
                    leq(trans_t, tt),
                    #geq(trans_t, tt-e)
                    leq(n, num_f_vec),
                    geq(n, 0),
                    # resource capacities
                    leq(sum(bw), 100),
                    leq(sum(proc), 150),
                    leq(sum(dur), 9),
                    geq(bw, 0),
                    geq(proc, 0),
                    geq(dur, 0),
                    # consts for dummy vars
                    geq(d1, 0),
                    leq(d1, 1000)
                  ]
                 )
  prog.show()
  print '(prog.objective).is_convex(): ', (prog.objective).is_convex()
  print '(prog.constraints).is_dcp(): ', (prog.constraints).is_dcp()
  prog.solve()
  print 'optimal point: '
  print 'tt: \n', tt.value
  print 'bw: \n', bw.value
  print 'proc: \n', proc.value
  print 'dur: \n', dur.value
  print 'n: \n', n.value
  print 'optimal value: '
  print 'trans_t: \n', trans_t.value
  # dummy var printout
  print 'd1: \n', d1.value
  #
  print 'F0: ', F0.value
  print 'F1: ', F1.value
  print 'F: ', F.value











if __name__ == "__main__":
  main()
