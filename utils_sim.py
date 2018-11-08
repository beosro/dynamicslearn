# Our infrastucture files
from utils_data import *

# data packages
import pickle
import random

# neural nets
from model_general_nn import GeneralNN, predict_nn
from model_split_nn import SplitModel
from _activation_swish import Swish
from model_ensemble_nn import EnsembleNN

# Torch Packages
import torch
import torch.nn as nn
from torch.nn import MSELoss

# timing etc
import time
import datetime
import os
import copy

# Plotting
import matplotlib.pyplot as plt
import matplotlib

def get_action(cur_state, model, method = 'Random'):
    # Returns an action for the robot given the current state and the model
    print("NOT DONE")

def plot_traj_model(df_traj, model):
    # plots all the states predictions over time

    data_params = {
        'states' : [],
        'inputs' : [],
        'change_states' : [],
        'battery' : True
    }

    X, U, dX = df_to_training(df_traj, data_params)

    # Gets starting state
    x0 = X[0,:]

    # get dims
    stack = int((len(X[0,:]))/9)
    xdim = 9
    udim = 4

    # store values
    pts = len(df_traj)
    x_stored = np.zeros((pts, stack*xdim))
    x_stored[0,:] = x0
    x_shift = np.zeros(len(x0))

    ####################### Generate Data #######################
    for t in range(pts-1):
        # predict
        x_pred = x_stored[t,:9]+ model.predict(x_stored[t,:], U[t,:])

        if stack > 1:
            # shift values
            x_shift[:9] = x_pred
            x_shift[9:-1] = x_stored[t,:-10]
        else:
            x_shift = x_pred

        # store values
        x_stored[t+1,:] = x_shift

    ####################### PLOT #######################
    with sns.axes_style("darkgrid"):
        ax1 = plt.subplot(331)
        ax2 = plt.subplot(332)
        ax3 = plt.subplot(333)
        ax4 = plt.subplot(334)
        ax5 = plt.subplot(335)
        ax6 = plt.subplot(336)
        ax7 = plt.subplot(337)
        ax8 = plt.subplot(338)
        ax9 = plt.subplot(339)

    plt.title("Comparing Dynamics Model to Ground Truth")

    ax1.set_ylim([-100,100])
    ax2.set_ylim([-100,100])
    ax3.set_ylim([-100,100])
    ax4.set_ylim([-35,35])
    ax5.set_ylim([-35,35])
    # ax6.set_ylim([-35,35])
    ax7.set_ylim([-10,10])
    ax8.set_ylim([-10,10])
    ax9.set_ylim([-0,20])

    ax1.plot(x_stored[:,0], linestyle = '--', color='b', label ='Predicted')
    ax1.plot(X[:,0], color = 'k', label = 'Ground Truth')

    ax2.plot(x_stored[:,1], linestyle = '--', color='b', label ='Predicted')
    ax2.plot(X[:,1], color = 'k', label = 'Ground Truth')

    ax3.plot(x_stored[:,2], linestyle = '--', color='b', label ='Predicted')
    ax3.plot(X[:,2], color = 'k', label = 'Ground Truth')

    ax4.plot(x_stored[:,3], linestyle = '--', color='b', label ='Predicted')
    ax4.plot(X[:,3], color = 'k', label = 'Ground Truth')

    ax5.plot(x_stored[:,4], linestyle = '--', color='b', label ='Predicted')
    ax5.plot(X[:,4], color = 'k', label = 'Ground Truth')

    ax6.plot(x_stored[:,5], linestyle = '--', color='b', label ='Predicted')
    ax6.plot(X[:,5], color = 'k', label = 'Ground Truth')

    ax7.plot(x_stored[:,6], linestyle = '--', color='b', label ='Predicted')
    ax7.plot(X[:,6], color = 'k', label = 'Ground Truth')

    ax8.plot(x_stored[:,7], linestyle = '--', color='b', label ='Predicted')
    ax8.plot(X[:,7], color = 'k', label = 'Ground Truth')

    ax9.plot(x_stored[:,8], linestyle = '--', color='b', label ='Predicted')
    ax9.plot(X[:,8], color = 'k', label = 'Ground Truth')

    ax1.legend()
    # ax2.plot(X[point:point+T+1,3:5])
    plt.show()


    quit()

class PID():
    def __init__(self, desired,
                    kp, ki, kd,
                    ilimit, outlimit,
                    dt, samplingRate, cutoffFreq = -1,
                    enableDFilter = False):

        # internal variables
        self.error = 0
        self.error_prev = 0
        self.integral = 0
        self.deriv = 0

        # constants
        self.desired = desired
        self.kp = kp
        self.ki = ki
        self.kd = kd

        # limits integral growth
        self.ilimit = ilimit

        # limits ridiculous actions. Should set to variance
        self.outlimit = outlimit

        # timee steps for changing step size of PID response
        self.dt = dt
        self.samplingRate = samplingRate    # sample rate is for filtering

        self.cutoffFreq = cutoffFreq
        self.enableDFilter = enableDFilter

        if cutoffFreq != -1 or enableDFilter:
            raise NotImplementedError('Have not implemnted filtering yet')

    def update(self, measured):

        # init
        out = 0.

        # update error
        self.error_prev = self.error

        # calc new error
        self.error = self.desired - measured

        # proportional gain is easy
        out += self.kp*self.error

        # calculate deriv term
        self.deriv = (self.error-self.error_prev) / self.dt

        # filtter if needed (DT function_)
        if self.enableDFilter:
            print('Do Filter')
            self.deriv = self.deriv

        # calcualte error value added
        out += self.deriv*self.kd

        # accumualte normalized eerror
        self.integral = self.error*self.dt

        # limitt the integral term
        if self.ilimit !=0:
            self.integral = np.clip(self.integral,-self.ilimit, self.ilimit)

        out += self.ki*self.integral

        # limitt the total output
        if self.outlimit !=0:
            out = np.clip(out,-self.outlimit, self.outlimit)

        return out

def pred_traj(x0, action, model, T):
    # get dims
    stack = int((len(x0))/9)
    xdim = 9
    udim = 4

    # figure out if given an action or a controller
    if not isinstance(action, np.ndarray):
        # given PID controller. Generate actions as it goes
        mode = 1

        PID = copy.deepcopy(action) # for easier naming and resuing code

        # create initial action
        action_eq = np.array([31687.1, 37954.7, 33384.8, 36220.11])
        action = np.array([31687.1, 37954.7, 33384.8, 36220.11])
        if stack > 1:
            action = np.tile(action, stack)
        action = np.concatenate((action,[3900]))

        # step 0 PID response
        action[:udim] += PID.update(x0[4])
    else:
        mode = 0

    # function to generate trajectories
    x_stored = np.zeros((T+1,len(x0)))
    x_stored[0,:] = x0
    x_shift = np.zeros(len(x0))

    for t in range(T):
        if mode == 1:
            # predict with actions coming from controller
            if stack > 1:       # if passed array of actions, iterate
                x_pred = x_stored[t,:9]+ model.predict(x_stored[t,:], action)

                # slide action here
                action[udim:-1] = action[:-udim-1]
            else:
                x_pred = x_stored[t,:9]+ model.predict(x_stored[t,:], action)

            # update action
            PIDout = PID.update(x_pred[4])
            action[:udim] = action_eq-np.array([1,1,-1,-1])*PIDout
            print("=== Timestep: ", t)
            print("Predicted angle: ", x_pred[4])
            print("PIDoutput: ", PIDout)
            print("Given Action: ", action[:udim])

        # else give action array
        elif mode == 0:
            # predict
            if stack > 1:       # if passed array of actions, iterate
                x_pred = x_stored[t,:9]+ model.predict(x_stored[t,:], action[t,:])
            else:
                x_pred = x_stored[t,:9]+ model.predict(x_stored[t,:], action)

        # shift values
        x_shift[:9] = x_pred
        x_shift[9:-1] = x_stored[t,:-10]

        # store values
        x_stored[t+1,:] = x_shift

    x_stored[:,-1] = x0[-1]     # store battery for all (assume doesnt change on this time horizon)

    return x_stored

def plot_voltage_context(model, df, action = [37000,37000, 30000, 45000], act_range = 25000, normalize = True, ground_truth = False):
    '''
    Takes in a dynamics model and plots the distributions of points in the dataset
      and plots various lines verses different voltage levels
    '''

    ################ Figure out what to do with the dataframe ################
    if 'vbat' not in df.columns.values:
        raise ValueError("This function requires battery voltage in the loaded dataframe for contextual plotting")

    ################# Make sure the model is in eval mode ################
    # model.eval()

    ################### Take the specific action rnage! #####################
    # going to need to set a specific range of actions that we are looking at.

    print("Looking around the action of: ", action, "\n    for a range of: ", act_range)

    # grab unique actions
    pwms_vals = np.unique(df[['m1_pwm_0', 'm2_pwm_0', 'm3_pwm_0', 'm4_pwm_0']].values)


    # grabs the actions within the range for each motor
    pwms_vals_range1 = pwms_vals[(pwms_vals < action[0]+act_range) & (pwms_vals > action[0]-act_range)]
    pwms_vals_range2 = pwms_vals[(pwms_vals < action[1]+act_range) & (pwms_vals > action[1]-act_range)]
    pwms_vals_range3 = pwms_vals[(pwms_vals < action[2]+act_range) & (pwms_vals > action[2]-act_range)]
    pwms_vals_range4 = pwms_vals[(pwms_vals < action[3]+act_range) & (pwms_vals > action[3]-act_range)]

    # filters the dataframe by these new conditions
    df_action_filtered = df.loc[(df['m1_pwm_0'].isin(pwms_vals_range1) &
                                 df['m2_pwm_0'].isin(pwms_vals_range2) &
                                 df['m3_pwm_0'].isin(pwms_vals_range3) &
                                 df['m4_pwm_0'].isin(pwms_vals_range4))]

    if len(df_action_filtered) == 0:
        raise ValueError("Given action not present in dataset")

    if len(df_action_filtered) < 10:
        print("WARNING: Low data for this action (<10 points)")

    print("Number of datapoints found is: ", len(df_action_filtered))


    ######################## batch data by rounding voltages ################
    # df = df_action_filtered.sort_values('vbat')
    df = df_action_filtered

    num_pts = len(df)

    # print("Battery voltages in play are:", np.unique(df['vbat'].values))
    print("Creating color gradient....")

    # spacing = np.linspace(0,num_pts,num_ranges+1, dtype=np.int)

    # parameters can be changed if desired
    data_params = {
        'states' : [],                      # most of these are to be implented for easily training specific states etc
        'inputs' : [],
        'change_states' : [],
        'battery' : True                    # Need to include battery here too
    }

    # this will hold predictions and the current state for ease of plotting
    predictions = np.zeros((num_pts, 2*9+1))

    X, U, dX = df_to_training(df, data_params)


    # gather predictions
    for n, (x, u, dx) in enumerate(zip(X, U, dX)):

        # predictions[i, n, 9:] = x[:9]+model.predict(x,u)
        if ground_truth:
            predictions[n, 9:-1] = dx
        else:
            # print('...')
            # print(x)
            # print(u)
            # print(model.predict(x,u))
            # print(model.predict(x,u))
            # print(dx)
            # print('^^^')
            predictions[n, 9:-1] = model.predict(x,u)
        predictions[n, :9] = x[:9]     # stores for easily separating generations from plotting
        predictions[n, -1] = u[-1]


    # if normalize, normalizes both the raw states and the change in states by
    #    the scalars stored in the model
    if normalize:
        scalarX, scalarU, scalardX = model.getNormScalers()
        prediction_holder = np.concatenate((predictions[:,:9],np.zeros((num_pts, (np.shape(X)[1]-9)))),axis=1)
        predictions[:,:9] = scalarX.transform(prediction_holder)[:,:9]
        predictions[:,9:-1] = scalardX.transform(predictions[:,9:-1])


    ######################### plot this dataset on Euler angles ################
    # this will a subplot with a collection of points showing the next state
    #   that originates from a initial state. The different battery voltages will
    #   be different colors. They could be lines, but is easier to thing about
    #   in an (x,y) case without sorting

    # plot properties
    font = {'size'   : 18}

    matplotlib.rc('font', **font)
    matplotlib.rc('lines', linewidth=2.5)

    ############## PLOT ALL POINTS ON 3 EULER ANGLES ###################
    if True:
        with sns.axes_style("darkgrid"):
            fig1, axes = plt.subplots(nrows=1, ncols=3, sharey=True)
            ax1, ax2, ax3 = axes[:]

            if ground_truth:
                plt.suptitle("Measured State Transitions Battery Voltage Context - Action: {0}".format(action))
                if normalize:
                    ax1.set_ylabel("Measured Normalized Change in State")
                else:
                    ax1.set_ylabel("Measured Change in state (Degrees)")
            else:
                plt.suptitle("Predicted State Transitions Battery Voltage Context - Action: {0}".format(action))
                if normalize:
                    ax1.set_ylabel("Predicted Normalized Change in State")
                else:
                    ax1.set_ylabel("Predicted Change in state (Degrees)")

            ax1.set_title("Pitch")
            ax2.set_title("Roll")
            ax3.set_title("Yaw")

            if normalize:
                ax1.set_xlabel("Normalized Pitch")
                ax2.set_xlabel("Normalized Roll")
                ax3.set_xlabel("Normalized Yaw")
                # ax1.set_xlim([-4,4])
                # ax2.set_xlim([-4,4])
                # ax3.set_xlim([-2,2])
                # ax1.set_xlim([-1,1])
                # ax2.set_xlim([-1,1])
                # ax3.set_xlim([-2,2])
                ax1.set_ylim([-1,1])
                ax2.set_ylim([-1,1])
                ax3.set_ylim([-1,1])
            else:
                ax1.set_xlabel("Global Pitch")
                ax2.set_xlabel("Global Roll")
                ax3.set_xlabel("Global Yaw")
                ax1.set_xlim([-45,45])
                ax2.set_xlim([-45,45])
                ax3.set_xlim([-180,180])

            fig1.subplots_adjust(right=0.8)
            cbar_ax1 = fig1.add_axes([0.85, 0.15, 0.02, 0.7])
            # ax1 = plt.subplot(131)
            # ax2 = plt.subplot(132)
            # ax3 = plt.subplot(133)

        # normalize batteris between 0 and 1
        # TODO: Figure out the coloring
        # predictions[:,:,-1] = (predictions[:,:,-1] - np.min(predictions[:,:,-1]))/(np.max(predictions[:,:,-1])-np.min(predictions[:,:,-1]))
        # print(predictions[:,:,-1])
        base = 50
        prec = 0
        vbats = np.around(base * np.around(predictions[:, -1]/base),prec)
        # vbats = predicitons[:,-1]
        hm = ax1.scatter(predictions[:,3], predictions[:,3+9], c=vbats, alpha = .7, s=3)
        ax2.scatter(predictions[:,4], predictions[:,4+9], c=vbats, alpha = .7, s=3)
        ax3.scatter(predictions[:,5], predictions[:,5+9], c=vbats, alpha = .7, s=3)
        cbar = fig1.colorbar(hm, cax=cbar_ax1)
        cbar.ax.set_ylabel('Battery Voltage (mV)')

        plt.show()

    ############## PLOT Pitch for battery cutoff ###################
    if True:
        battery_cutoff = 3800
        battery_cutoff = int(np.mean(predictions[:, -1]))
        battery_cutoff = int(np.median(predictions[:, -1]))

        print("Plotting Pitch Dynamics for Above and Below {0} mV".format(battery_cutoff))
        with sns.axes_style("darkgrid"):
            fig2, axes2 = plt.subplots(nrows=1, ncols=2, sharey=True)
            ax21, ax22 = axes2[:]

            if ground_truth:
                plt.suptitle("Measured Pitch Transitions Above and Below Mean Vbat: {0}".format(battery_cutoff))
                if normalize:
                    ax21.set_ylabel("Normalized Measured Change in State")
                else:
                    ax21.set_ylabel("Measured Change in state (Degrees)")
            else:
                plt.suptitle("Predicted Pitch Transitions Above and Below Mean Vbat: {0}".format(battery_cutoff))
                if normalize:
                    ax21.set_ylabel("Normalized Predicted Change in State")
                else:
                    ax21.set_ylabel("Predicted Change in state (Degrees)")

            ax21.set_title("Pitch, Vbat < {0}".format(battery_cutoff))
            ax22.set_title("Pitch, Vbat > {0}".format(battery_cutoff))

            if normalize:
                ax21.set_xlabel("Normalized Pitch")
                ax22.set_xlabel("Normalized Pitch")
                # ax21.set_xlim([-4,4])
                # ax22.set_xlim([-4,4])
                ax21.set_ylim([-1,1])
                ax22.set_ylim([-1,1])
            else:
                ax21.set_xlabel("Global Pitch")
                ax22.set_xlabel("Global Pitch")
                ax21.set_xlim([-45,45])
                ax22.set_xlim([-45,45])

            fig2.subplots_adjust(right=0.8)
            cbar_ax = fig2.add_axes([0.85, 0.15, 0.02, 0.7])

        base = 50
        prec = 1
        vbats = np.around(base * np.around(predictions[:, -1]/base),prec)
        flag = vbats > battery_cutoff
        notflag = np.invert(flag)
        # hm2 = plt.scatter(predictions[:,3], predictions[:,3+9], c=predictions[:, -1], alpha = .7, s=3)
        # plt.clf()
        ax21.scatter(predictions[flag,3], predictions[flag,3+9], c=vbats[flag], alpha = .7, s=3)
        ax22.scatter(predictions[notflag,3], predictions[notflag,3+9], c=vbats[notflag], alpha = .7, s=3)
        cbar = fig2.colorbar(hm, cax=cbar_ax)
        cbar.ax.set_ylabel('Battery Voltage (mV)')

        #########
        plt.show()

    # TODO: Make big plot of one dimension where each subplot is of 50 mv steps

    raise NotImplementedError("tbd")
