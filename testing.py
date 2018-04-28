from dynamics import *
from controllers import randController, MPController
from dynamics_ionocraft import IonoCraft
from dynamics_crazyflie_linearized import CrazyFlie
from utils_plot import *
from utils_data import *
from models import LeastSquares

# Plotting
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


### EXAMPLE EXECUTION

################################ INITIALIZATION ################################
print('\n')
print('---begin--------------------------------------------------------------')

# initialize some variables
dt_x = .0025
dt_u = .01
print('Simulation update step is: ', dt_x, ' and contorl update is: ', dt_u)
# dynamics object
iono1 = IonoCraft(dt_x, x_noise = .0001)

mgo4 = iono1.m*iono1.g/4

# initial state is origin
x0 = np.zeros(12)
u0 = np.array([mgo4+.0001,mgo4,mgo4,mgo4]) #np.zeros(4)

# good for unit testin dynamics
x1 = iono1.simulate(x0,u0)
# x1[x1 < .00001] = 0
x2 = iono1.simulate(x1,u0)
# x2[x2 < .00001] = 0
x3 = iono1.simulate(x2,u0)

# prints state in readible form
printState(x3)

# Simulate data for training
N = 250     # num sequneces

# generate training data
Seqs_X, Seqs_U = generate_data(iono1, dt_control = dt_u, sequence_len=25, num_iter = N)

# converts data from list of trajectories of [next_states, states, inputs]
#       to a large array of [next_states, states, inputs]
data = sequencesXU2array(Seqs_X, Seqs_U)

# Check shape of data
# print(np.shape(data))

################################ LEARNING ################################


# create a learning model
lin1 = LeastSquares()

# train it like this
lin1.train(l2array(data[:,0]),l2array(data[:,1]),l2array(data[:,2]))

################################ Obj Fnc ################################

origin_minimizer = Objective(np.linalg.norm, 'min', 3, dim_to_eval=[0, 1, 2])

################################ MPC ################################

# # initialize MPC object with objective function above
# mpc1 = MPController(lin1, iono1, origin_minimizer)
#
# x0 = np.zeros(12)
# new_seq, Us = sim_sequence(iono1, sequence_len = 50, x0=x0, controller = mpc1)
#
# compareTraj(Us, x0, iono1, lin1, show=True)
################################ Sim Controlled ################################

# Sim sequence off the trained controller
x_controlled, u_seq = sim_sequence(iono1, controller = randController(iono1, dt_u), sequence_len = 100, to_print = False)
print(u_seq)

################################ PLot ################################

# plot states and inputs of the trajectory if wanted
# T = np.linspace(0,N*dt,N)
# plot12(X, T)
# plotInputs(U, T)

# Plots animation, change save to false to not save .gif
# plotter1 = PlotFlight(x_controlled,.5)
# plotter1.show(save=True)


print('---------------------------------------------------------end run-----')
