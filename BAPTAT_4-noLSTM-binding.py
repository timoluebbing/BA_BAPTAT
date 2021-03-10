# packet imports 
import numpy as np
from numpy.lib.function_base import append 
import torch
import copy
from torch import nn, autograd
from torch.autograd import Variable
from torch._C import device
import matplotlib.pyplot as plt

# class imports 
from BinAndPerspTaking.binding import Binder
from BinAndPerspTaking.binding_exmat import BinderExMat
from BinAndPerspTaking.perspective_taking import Perspective_Taker
from CoreLSTM.core_lstm import PSEUDO_CORE
from Data_Compiler.data_preparation import Preprocessor
from BAPTAT_evaluation import BAPTAT_evaluator

############################################################################
##########  PARAMETERS  ####################################################

## General parameters 
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
autograd.set_detect_anomaly(True)

torch.set_printoptions(precision=8)


## Define data parameters
num_frames = 100
num_input_features = 15
num_input_dimensions = 3
preprocessor = Preprocessor(num_input_features, num_input_dimensions)
evaluator = BAPTAT_evaluator(num_frames, num_input_features, preprocessor)
data_at_unlike_train = False ## Note: sample needs to be changed in the future

# data paths 
data_asf_path = 'Data_Compiler/S35T07.asf'
data_amc_path = 'Data_Compiler/S35T07.amc'


## Define tuning parameters 
tuning_length = 10      # length of tuning horizon 
tuning_cycles = 3       # number of tuning cycles in each iteration 

# possible loss functions
mse = nn.MSELoss()
l1Loss = nn.L1Loss()
l2Loss = lambda x,y: mse(x, y) * (num_input_dimensions * num_input_features)

# define learning parameters 
at_loss_function = l1Loss
at_learning_rate = 1
bm_momentum = 0.0


## Define tuning variables
# general
obs_count = 0
at_inputs = torch.tensor([])
at_predictions = torch.tensor([])
at_final_predictions = torch.tensor([])
at_losses = []

# binding
bindSM = nn.Softmax(dim=0)  # columnwise
binder = BinderExMat(num_features=num_input_features, gradient_init=True)
ideal_binding = torch.Tensor(np.identity(num_input_features))

Bs = []
B_grads = [None] * (tuning_length+1)
B_upd = [None] * (tuning_length+1)
bm_losses = []
bm_dets = []



############################################################################
##########  INITIALIZATIONS  ###############################################

## Load data
observations, feature_names = preprocessor.get_AT_data(data_asf_path, data_amc_path, num_frames+2)
div_observations = preprocessor.get_motion_data(observations, num_frames+2)    

## Load model
core_model = PSEUDO_CORE()


## Binding matrices 
# Init binding entries 
be = binder.init_binding_entries_det_()
print(be)

for i in range(tuning_length+1):
    entries = []
    for j in range(num_input_features):
        row = []
        for k in range(num_input_features):
            entry = be[j][k].clone()
            entry.requires_grad_()
            row.append(entry)
        entries.append(row)
    Bs.append(entries)
    
# print(f'BMs different in list: {Bs[0] is not Bs[1]}')


############################################################################
##########  FORWARD PASS  ##################################################

for i in range(tuning_length):
    o = observations[obs_count]
    div_o_next = div_observations[obs_count]
    at_inputs = torch.cat((at_inputs, o.reshape(1, num_input_features, num_input_dimensions)), 0)
    obs_count += 1

    bm = binder.compute_binding_matrix(Bs[i], bindSM)
    x_B = binder.bind(o, bm)

    new_prediction = core_model.forward(x_B, bm.clone().detach(), o.clone().detach(), div_o_next)  
    at_predictions = torch.cat((at_predictions, new_prediction.reshape(1,num_input_features, num_input_dimensions)), 0)

############################################################################
##########  ACTIVE TUNING ##################################################

while obs_count < num_frames:
    # TODO folgendes evtl in function auslagern
    o = observations[obs_count]
    div_o_next = div_observations[obs_count]
    obs_count += 1

    bm = binder.compute_binding_matrix(Bs[-1], bindSM)
    x_B = binder.bind(o, bm)
    
    ## Generate current prediction 
    with torch.no_grad():
        new_prediction = core_model.forward(x_B, bm.clone().detach(), o.clone().detach(), div_o_next)

    ## For #tuning_cycles 
    for cycle in range(tuning_cycles):
        print('----------------------------------------------')

        # Get prediction
        p = at_predictions[-1]

        # Calculate error 
        lam = 10
        # loss = at_loss_function(p, x[0]) + l1Loss(p,x[0]) + lam / torch.norm(torch.Tensor(Bs[0].copy()))
        # loss = at_loss_function(p, x[0]) + mse(p, x[0])
        # loss = l1Loss(p,x[0]) + l2Loss(p,x[0])
        # loss_scale = torch.square(torch.mean(torch.norm(torch.tensor(Bs[-1]), dim=1, keepdim=True)) -1.) ##COPY?????
        loss_scale = torch.square(torch.mean(torch.norm(bm.clone().detach(), dim=1, keepdim=True)) -1.) ##COPY?????
        # -> länge der Vektoren 
        print(f'loss scale: {loss_scale}')
        loss_scale_factor = 0.9
        l1scale = loss_scale_factor * loss_scale
        l2scale = loss_scale_factor / loss_scale
        # loss = l1Loss(p,x[0]) + l2scale * l2Loss(p,x[0])
        # loss = l1scale * mse(p,x[0]) + l2scale * l2Loss(p,x[0])
        # loss = l2Loss(p,x[0]) + mse(p,x[0])
        # loss = l2Loss(p,x[0]) + loss_scale * mse(p,x[0])
        # print(p.shape)
        # print(x_B.shape)
        loss = loss_scale_factor * loss_scale * l2Loss(p,x_B) + mse(p,x_B)
        # loss = loss_scale_factor * loss_scale * (l2Loss(p,x[0]) + mse(p,x[0]))
        # loss = loss_scale_factor * loss_scale * l2Loss(p,x[0]) 
        # loss = loss_scale_factor * loss_scale * mse(p,x[0])
        at_losses.append(loss)
        print(f'frame: {obs_count} cycle: {cycle} loss: {loss}')

        # Propagate error back through tuning horizon 
        loss.backward(retain_graph = True)

        # Update parameters 
        with torch.no_grad():
            
            # Calculate gradients with respect to the entires 
            for i in range(tuning_length+1):
                grad = []
                for j in range(num_input_features):
                    row = []
                    for k in range(num_input_features):
                        row.append(Bs[i][j][k].grad)
                    grad.append(torch.stack(row))
                B_grads[i] = torch.stack(grad)

            # print(B_grads[tuning_length])
            
            # Calculate overall gradients 
            ### version 0
            # grad_B = B_grads[-1]
            ### version 1
            # grad_B = B_grads[0]
            ### version 2 / 3
            # grad_B = torch.mean(torch.stack(B_grads), 0)
            ### version 4
            # # # # bias > 1 => favor recent
            # # # # bias < 1 => favor earlier
            # # # # bias = 1 => average
            bias = 1.5
            weighted_grads_B = [None] * (tuning_length+1)
            for i in range(tuning_length+1):
                weighted_grads_B[i] = np.power(bias, i) * B_grads[i]
            grad_B = torch.mean(torch.stack(weighted_grads_B), dim=0)
            
            # print(f'grad_B: {grad_B}')
            # print(f'grad_B: {torch.norm(grad_B, 1)}')
            

            # Update parameters in time step t-H with saved gradients 
            upd_B = binder.update_binding_entries_(Bs[0], grad_B, at_learning_rate, bm_momentum)

            # Compare binding matrix to ideal matrix
            c_bm = binder.compute_binding_matrix(upd_B, bindSM)
            mat_loss = evaluator.FBE(c_bm, ideal_binding)
            bm_losses.append(mat_loss)
            print(f'loss of binding matrix (FBE): {mat_loss}')

            # Compute determinante of binding matrix
            det = torch.det(c_bm)
            bm_dets.append(det)
            print(f'determinante of binding matrix: {det}')
            
            
            # Zero out gradients for all parameters in all time steps of tuning horizon
            for i in range(tuning_length+1):
                for j in range(num_input_features):
                    for k in range(num_input_features):
                        Bs[i][j][k].requires_grad = False
                        Bs[i][j][k].grad.data.zero_()

            # Update all parameters for all time steps 
            for i in range(tuning_length+1):
                entries = []
                for j in range(num_input_features):
                    row = []
                    for k in range(num_input_features):
                        entry = upd_B[j][k].clone()
                        entry.requires_grad_()
                        row.append(entry)
                    entries.append(row)
                Bs[i] = entries
            
            # print(Bs[0])

        
        ## REORGANIZE FOR MULTIPLE CYCLES!!!!!!!!!!!!!

        # forward pass from t-H to t with new parameters 
        for i in range(tuning_length):

            bm = binder.compute_binding_matrix(Bs[i], bindSM)
            x_B = binder.bind(o, bm)

            # print(f'x_B :{x_B}')
            div_o = div_observations[obs_count-1-(tuning_length+i)]
            at_predictions[i] = core_model.forward(x_B, bm.clone().detach(), o.clone().detach(), div_o)
            

        # Update current binding
        bm = binder.compute_binding_matrix(Bs[-1], bindSM)
        x_B = binder.bind(o, bm)


    # END tuning cycle        

    ## Generate updated prediction 
    new_prediction = core_model.forward(x_B, bm.clone().detach(), o.clone().detach(), div_o_next)

    ## Reorganize storage variables
   
    # observations
    at_inputs = torch.cat((at_inputs[1:], o.reshape(1, num_input_features, num_input_dimensions)), 0)
    
    # predictions
    at_final_predictions = torch.cat((at_final_predictions, at_predictions[0].reshape(1,45)), 0)
    at_predictions = torch.cat((at_predictions[1:], new_prediction.reshape(1,num_input_features, num_input_dimensions)), 0)

# END active tuning
    
# store rest of predictions in at_final_predictions
for i in range(tuning_length): 
    at_final_predictions = torch.cat((at_final_predictions, at_predictions[1].reshape(1,45)), 0)

# get final binding matrix
final_binding_matrix = binder.compute_binding_matrix(Bs[-1], bindSM)
print(f'final binding matrix: {final_binding_matrix}')
final_binding_entires = torch.tensor(Bs[-1])
print(f'final binding entires: {final_binding_entires}')


############################################################################
##########  EVALUATION #####################################################
pred_errors = evaluator.prediction_errors(observations, 
                                          at_final_predictions, 
                                          at_loss_function)

evaluator.plot_at_losses(at_losses, 'History of overall losses during active tuning')
evaluator.plot_at_losses(bm_losses, 'History of binding matrix loss (FBE)')
evaluator.plot_at_losses(bm_dets, 'History of binding matrix determinante')

evaluator.plot_binding_matrix(
    final_binding_matrix, 
    feature_names, 
    'Binding matrix showing relative contribution of observed feature to input feature'
)
evaluator.plot_binding_matrix(
    final_binding_entires, 
    feature_names, 
    'Binding matrix entries showing contribution of observed feature to input feature'
)

# evaluator.help_visualize_devel(observations, at_final_predictions)