import numpy as np
import torch 
from torch import nn
from datetime import datetime
import os
import pandas as pd

import sys

sys.path.append('D:/Uni/Kogni/Bachelorarbeit/Code/BA_BAPTAT')
from interfaces.general_interface import TESTER
from Testing.TESTING_statistical_evaluation_abstract import TEST_STATISTICS


class COMP_BINDING_SCALE_GEST(TESTER): 

    def __init__(self, num_features, num_observations, num_dimensions):
        experiment_name = f"compare_binding_sig_rw_cw_rcw_dim{num_dimensions}"
        super().__init__(num_features, num_observations, num_dimensions, experiment_name)
        self.stats = TEST_STATISTICS(self.num_features, self.num_observations, self.num_dimensions)
        print('Initialized experiment.')


    def perform_experiment(self, sample_nums, modification, scalers): 

        ## General parameters
        # possible loss functions
        mse = nn.MSELoss()
        l1Loss = nn.L1Loss()
        smL1Loss = nn.SmoothL1Loss(reduction='sum')
        l2Loss = lambda x,y: self.mse(x, y) * (self.num_dimensions * self.num_observations)

        # possible models to use 
        if self.num_dimensions == 7:
            self.model_path = 'CoreLSTM/models/ADAM/LSTM_24_gest.pt'
        elif self.num_dimensions == 6:
            self.model_path = 'CoreLSTM/models/ADAM/LSTM_25_vel.pt'
        elif self.num_dimensions == 3: 
            self.model_path = 'CoreLSTM/models/ADAM/LSTM_26_pos.pt'
        else: 
            print('ERROR: Unvalid number of dimensions!\nPlease use 3, 6, or 7.')
            exit()

        ## Experiment parameters
        # NOTE: set manually, for all parameters that are not tested

        tuning_length = 20
        num_tuning_cycles = 3
        # at_loss_function = mse
        at_loss_function = nn.SmoothL1Loss(reduction='sum', beta=0.0001)
        loss_parameters = [('beta', 0.0001), ('reduction', 'sum')]

        # rotation_type = 'eulrotate'
        rotation_type = 'qrotate'

        at_learning_rate_binding = 0.1
        at_learning_rate_rotation =  0.1
        at_learning_rate_translation = 1
        at_learning_rate_state = 0.0

        at_momentum_binding = 0.9
        at_momentum_rotation = 0.8
        at_momentum_translation = 0.3

        grad_calc_binding = 'weightedInTunHor'
        grad_calc_rotation = 'weightedInTunHor'
        grad_calc_translation = 'meanOfTunHor'
        grad_calculations = [grad_calc_binding, grad_calc_rotation, grad_calc_translation]
        
        grad_bias_binding = 1.4
        grad_bias_rotation = 1.1
        grad_bias_translation = 1.5 
        grad_biases = [grad_bias_binding, grad_bias_rotation, grad_bias_translation]

        nxm_bool = False
        index_additional_features = [6]
        initial_value_dummie_line = 0.1
        nxm_enhancement = 'square'
        nxm_outcast_line_scaler = 0.1

        experiment_results = []

        ## experiment performed for all values of the tested parameter
        changed_parameter = 'scaler'
        parameter_values = scalers
        for scaler in scalers: 
            # set value of tested parameter
            self.BAPTAT.set_scale_mode(scaler)
         
            print(f'New scaler for binding matrix: {scaler}')

            # set BAPTAT parameters
            self.BAPTAT.set_weighted_gradient_biases(grad_biases)        

            if nxm_bool:
                self.BAPTAT.set_additional_features(index_additional_features)
                self.BAPTAT.set_dummie_init_value(initial_value_dummie_line)
                self.BAPTAT.set_nxm_enhancement(nxm_enhancement)
                self.BAPTAT.set_nxm_last_line_scale(nxm_outcast_line_scaler) 

            # run experiment
            sample_names, result_names, results = super().run(
                changed_parameter+"_"+str(scaler)+"/",
                modification,
                sample_nums, 
                self.model_path, 
                tuning_length, 
                num_tuning_cycles, 
                at_loss_function,
                loss_parameters,
                [at_learning_rate_binding, at_learning_rate_rotation, at_learning_rate_translation], 
                at_learning_rate_state, 
                [at_momentum_binding, at_momentum_rotation, at_momentum_translation],
                grad_calculations
            )

            experiment_results += [results]

        
        ## statistics and comparison plots 

        dfs = self.stats.load_csvresults_to_dataframe(
            self.prefix_res_path, 
            changed_parameter, 
            parameter_values, 
            sample_names, 
            result_names
            )


        self.stats.plot_histories(
            dfs, 
            self.prefix_res_path, 
            changed_parameter, 
            result_names, 
            result_names
        )

        self.stats.plot_value_comparisons(
            dfs, 
            self.prefix_res_path, 
            changed_parameter, 
            result_names, 
            result_names
        )

        print("Terminated experiment.")


            
       
def main(): 
    # set the following parameters
    num_observations = 15
    num_input_features = 15
    num_dimensions = 7

    test = COMP_BINDING_SCALE_GEST(
        num_input_features, 
        num_observations, 
        num_dimensions) 

    
    modification = [
        ('bind', None, None)           
        # ('bind', 'det', None) 
        # ('bind', 'rand', None) 
    ]

    sample_nums = [990]
    # sample_nums = [990, 550]

    scalers = ['sigmoid',  'rcwSM']
    # scalers = ['sigmoid', 'rwSM', 'cwSM', 'rcwSM']

    test.perform_experiment(sample_nums, modification, scalers)

    

if __name__ == "__main__":
    main()