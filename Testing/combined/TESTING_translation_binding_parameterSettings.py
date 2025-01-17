import numpy as np
import torch 
from torch import nn
from datetime import datetime
import os
import pandas as pd

import sys

sys.path.append('D:/Uni/Kogni/Bachelorarbeit/Code/BA_BAPTAT')
from interfaces.combined_interface import TEST_COMBINATIONS


class TEST_COMBI_ALL_PARAMS(TEST_COMBINATIONS): 

    def __init__(self, num_features, num_observations, num_dimensions):
        experiment_name = "combination_t_b_parameter_settings"
        super().__init__(num_features, num_observations, num_dimensions, experiment_name)

        print('Initialized experiment.')


    def perform_experiment(self, sample_nums, changed_parameter, parameter_values): 

        ## General parameters
        # possible loss functions
        mse = nn.MSELoss()
        l1Loss = nn.L1Loss()
        smL1Loss = nn.SmoothL1Loss(reduction='sum')
        l2Loss = lambda x,y: self.mse(x, y) * (self.num_dimensions * self.num_observations)

        # set manually
        modification = [
            ('bind', 'det', None), 
            ('translate', 'det', range(5))
        ]

        model_path = 'CoreLSTM/models/LSTM_46_cell.pt'
        tuning_length = 10
        num_tuning_cycles = 3
        at_loss_function = nn.SmoothL1Loss(reduction='sum', beta=0.8)
        loss_parameters = [('beta', 0.8), ('reduction', 'sum')]

        at_learning_rate_binding = 1
        at_learning_rate_translation = 0.1
        at_learning_rate_state = 0.1

        at_momentum_binding = 0.9
        at_momentum_translation = 0.0

        grad_calc_binding = 'weightedInTunHor'
        grad_calc_translation = 'meanOfTunHor'
        grad_calculations = [grad_calc_binding, None, grad_calc_translation]
        
        grad_bias_binding = 1.5
        grad_bias_translation = 1.5 
        grad_biases = [grad_bias_binding, None, grad_bias_translation]


        for val in parameter_values: 
            if changed_parameter == 'model_path': 
                model_path = val
            elif changed_parameter == 'modification': 
                modification = val
            elif changed_parameter == 'rotation_type': 
                rotation_type = val
            elif changed_parameter == 'tuning_length': 
                tuning_length = val
            elif changed_parameter == 'num_tuning_cycles': 
                num_tuning_cycles = val
            elif changed_parameter == 'at_loss_function': 
                at_loss_function = val
            elif changed_parameter == 'loss_parameters': 
                [(_, beta_val), (_, reduction_val)] = loss_parameters
                at_loss_function = nn.SmoothL1Loss(reduction=reduction_val, beta=beta_val)
            elif changed_parameter == 'at_learning_rate_binding': 
                at_learning_rate_binding = val
            elif changed_parameter == 'at_learning_rate_translation': 
                at_learning_rate_translation = val
            elif changed_parameter == 'at_learning_rate_state': 
                at_learning_rate_state = val
            elif changed_parameter == 'at_momentum_binding': 
                at_momentum_binding = val  
            elif changed_parameter == 'at_momentum_translation': 
                at_momentum_translation = val 
            elif changed_parameter == 'grad_calculations': 
                grad_calculations = val  
            elif changed_parameter == 'grad_biases': 
                grad_biases = val  
            else: 
                print('Unknown parameter!')
                break       

            print(f'New value for {changed_parameter}: {val}')

            self.BAPTAT.set_weighted_gradient_biases(grad_biases)  

            results = super().run(
                changed_parameter+"_"+str(val)+"/",
                modification,
                sample_nums, 
                model_path, 
                tuning_length, 
                num_tuning_cycles, 
                at_loss_function,
                loss_parameters,
                [at_learning_rate_binding, None, at_learning_rate_translation], 
                at_learning_rate_state, 
                [at_momentum_binding, None, at_momentum_translation],
                grad_calculations
            )


        print("Terminated experiment.")
            
      
def main(): 
    num_observations = 15
    num_input_features = 15
    num_dimensions = 3
    test = TEST_COMBI_ALL_PARAMS(
        num_observations, 
        num_input_features, 
        num_dimensions) 

    
    # sample_nums = [1000, 250, 300] 
    # sample_nums = [1000,550,450]
    # sample_nums = [100,100,100]
    # sample_nums = [20,20,20]
    # sample_nums = [50,50,50]
    # sample_nums = [15,15,15]
    # sample_nums = [12,12,12]
    sample_nums = [500]

    tested_parameter = 'num_tuning_cycles'
    parameter_values = [3]

    # tested_parameter = 'at_loss_function'
    # parameter_values = [nn.SmoothL1Loss(reduction='sum', beta=0.8), nn.MSELoss()]

    # tested_parameter = 'loss_parameters'
    # parameter_values = [
    #     [('beta', 0.4),('reduction', 'mean')], 
    #     [('beta', 0.6),('reduction', 'mean')], 
    #     [('beta', 0.8),('reduction', 'mean')], 
    #     [('beta', 1.0),('reduction', 'mean')]
    #     [('beta', 1.2),('reduction', 'mean')], 
    # ]

    # tested_parameter = 'at_learning_rate_binding'
    # parameter_values = [1, 0.1, 0.01]


    # tested_parameter = 'at_learning_rate_translation'
    # parameter_values = [1, 0.1]




    test.perform_experiment(sample_nums, tested_parameter, parameter_values)

    

if __name__ == "__main__":
    main()