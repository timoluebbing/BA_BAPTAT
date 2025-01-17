import torch
from torch import nn
import matplotlib.pyplot as plt

import sys
sys.path.append('D:/Uni/Kogni/Bachelorarbeit/Code/BA_BAPTAT')
from CoreLSTM.core_lstm import CORE_NET
from Data_Compiler.data_preparation import Preprocessor
from Data_Compiler.skeleton_renderer import SKEL_RENDERER


class LSTM_Tester(): 

    def __init__(self, loss_function, num_dimensions,num_features):
        self._loss_function = loss_function
        self.num_dimensions = num_dimensions
        self.num_features = num_features
        self.renderer = SKEL_RENDERER()


    def predict(self, num_predictions, model, test_input, test_target, train_window): 
        prediction_error = []
        state = model.init_hidden(train_window)
        state_scale = 0.9
        for i in range(num_predictions):
            seq = test_input[-train_window:]

            with torch.no_grad():
                if i>0:
                    loss = self._loss_function(test_input[-1], test_target[0,i]).item()
                    prediction_error.append(loss)

                state = (state[0] * state_scale, state[1] * state_scale)
                new_prediction, state = model(seq, state)
                test_input = torch.cat((test_input, new_prediction[-1].reshape(1,45)), 0)

        predictions = test_input[-num_predictions:].reshape(num_predictions, 15, 3)
        self.renderer.render(predictions)

        return predictions, prediction_error

    
    def predict(self, num_predictions, model, test_input, test_target, train_window): 
        prediction_error = []
        prediction_error_position = []
        prediction_error_direction = []
        prediction_error_magnitude = []
        state = model.init_hidden(train_window)
        state_scale = 0.9
        for i in range(num_predictions):
            seq = test_input[-train_window:]

            with torch.no_grad():
                if i>0:
                    loss = self._loss_function(test_input[-1], test_target[0,i]).item()
                    prediction_error.append(loss)

                    last_test_input = test_input[-1].view(self.num_features,self.num_dimensions)
                    current_test_target = test_target[0,i].view(self.num_features,self.num_dimensions)

                    # print(test_input.shape)
                    # print(test_target.shape)
                    # print(test_input[-1])
                    # print(test_input[-1, :3])
                    # print(test_input[-1, 3:6])
                    # print(test_input[-1, -1])
                    loss = self._loss_function(last_test_input[:,:3], current_test_target[:,:3]).item()
                    prediction_error_position.append(loss)

                    if self.num_dimensions >3:
                        loss = self._loss_function(last_test_input[:,3:6], current_test_target[:,3:6]).item()
                        prediction_error_direction.append(loss)

                        if self.num_dimensions >6:
                            loss = self._loss_function(last_test_input[:,-1], current_test_target[:,-1]).item()
                            prediction_error_magnitude.append(loss)


                state = (state[0] * state_scale, state[1] * state_scale)
                new_prediction, state = model(seq, state)
                test_input = torch.cat((test_input, new_prediction[-1].reshape(1,self.num_dimensions*self.num_features)), 0)

        predictions = test_input[-num_predictions:].reshape(num_predictions, self.num_features, self.num_dimensions)
        if self.num_dimensions == 3:
            self.renderer.render(predictions, None, None, False)

        else:    
            pos = predictions[:,:,:3]
            dir = predictions[:,:,3:6]
            if self.num_dimensions > 6:
                mag = predictions[:,:,-1]
            else: 
                mag = torch.ones(pos.size()[0], pos.size()[1], 1)
            
            self.renderer.render(pos, dir, mag, True)

        return predictions, prediction_error, prediction_error_position, prediction_error_direction, prediction_error_magnitude

    
    def plot_pred_error(self, errors):
        fig = plt.figure()
        axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) 
        axes.plot(errors, 'r')
        axes.grid(True)
        axes.set_xlabel('time steps')
        axes.set_ylabel('prediction error')
        axes.set_title('Prediction error during testing')
        plt.show()

    
    def test(self, num_predictions, model_path, test_input, test_target, train_window, hidden_num):
        model = CORE_NET(input_size=self.num_features*self.num_dimensions, hidden_layer_size=hidden_num)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        print(model)

        pred, pred_err, pred_err_pos, pred_err_dir, pred_err_mag  = self.predict(num_predictions, model, test_input, test_target, train_window)

        self.plot_pred_error(pred_err)
        self.plot_pred_error(pred_err_pos)
        self.plot_pred_error(pred_err_dir)
        self.plot_pred_error(pred_err_mag)



def main():
    # LSTM parameters
    frame_samples = 1000
    train_window = 50
    testing_size = 100
    num_features = 15
    num_dimensions = 3
    loss_function=nn.MSELoss()

    # Init tools
    prepro = Preprocessor(num_features=num_features, num_dimensions=num_dimensions)
    tester = LSTM_Tester(loss_function)

    # Init tools
    data_asf_path = 'Data_Compiler/S35T07.asf'
    data_amc_path = 'Data_Compiler/S35T07.amc'
    model_save_path = 'CoreLSTM/models/LSTM_26_cell.pt'

    # Preprocess data
    io_seq, dt_train, dt_test = prepro.get_LSTM_data(data_asf_path, 
                                                    data_amc_path, 
                                                    frame_samples, 
                                                    testing_size, 
                                                    train_window)

    test_input = dt_train[0,-train_window:]

    # Test LSTM
    tester.test(testing_size, model_save_path, test_input, dt_test, train_window)
    


if __name__ == "__main__":
    main()