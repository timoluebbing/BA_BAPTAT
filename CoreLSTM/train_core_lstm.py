import torch 
from torch import nn
import matplotlib.pyplot as plt

import sys
# sys.path.append('D:/Uni/Kogni/Bachelorarbeit/Code/BA_BAPTAT')
sys.path.append('C:/Users/TimoLuebbing/Desktop/BA_BAPTAT')
from CoreLSTM.core_lstm import CORE_NET
from CoreLSTM.test_core_lstm import LSTM_Tester
from Data_Compiler.data_preparation import Preprocessor
from torch.utils.data import TensorDataset, DataLoader


class LSTM_Trainer():
    ## General parameters 
    device = torch.device('cpu') # 'cuda' if torch.cuda.is_available() else 

    def __init__(self, loss_function, learning_rate, momentum, l2_penality, batch_size):
        self._model = CORE_NET()
        self.batch_size = batch_size
        self._loss_function = loss_function
        self._optimizer = torch.optim.SGD(self._model.parameters(), lr=learning_rate, momentum=momentum, weight_decay=l2_penality)
        # self._optimizer = torch.optim.SGD(self._model.parameters(), lr=learning_rate)
        # self._optimizer = torch.optim.Adam(self._model.parameters(), lr=learning_rate)

        print('Initialized model!')
        print(self._model)
        print(self._loss_function)
        print(self._optimizer)


    def train(self, epochs, train_sequence, save_path):
        losses = []
        num_batches = len(train_sequence)
        # print(num_batches)
        for ep in range(epochs):
            self._model.zero_grad()
            self._optimizer.zero_grad()
            ep_loss = 0

            #########################################################################################
            # Teacher Forcing
            inputs = []
            targets = []
            for seq, labels in train_sequence:
                inputs.append(seq)
                # print(seq[1:,:].shape)
                # print(labels.shape)
                target = torch.cat((seq[1:,:], labels), dim=0)
                targets.append(target)
            
            batch_size = seq.size()[0]
            ins = []
            tars = []
            for i in range(len(train_sequence)):
                if i%batch_size==0:
                    ins.append(inputs[i])
                    tars.append(targets[i])
            ins = torch.stack(ins)
            tars = torch.stack(tars)
            num_batches = ins.size()[0]
            num_input = ins.size()[2]
            # print(num_batches)
            state = self._model.init_hidden(num_batches)
            # print(ins.shape)
            # print(tars.shape)
            
            outs = []
            for i in range(batch_size):
                input = ins[:,i,:].view(num_batches, num_input)
                # print(input.shape)
                out, state = self._model.forward(input, state)
                outs.append(out)

            outs = torch.stack(outs)
            single_loss = self._loss_function(outs, tars.permute(1,0,2))
            single_loss.backward()
            self._optimizer.step()
            # print(single_loss.item())

            ep_loss = single_loss 

            #########################################################################################
            # Update State nach jedem Batch mit End-Prediction, inkl. Teacher Forcing 
            # DISTINCT! but same batches every epoch! 
            # inputs = []
            # targets = []
            # i = 0
            # batch_size = train_sequence[0][0].size()[0]
            # for seq, labels in train_sequence:
            #     if i%batch_size==0:
            #         inputs.append(seq)
            #         targets.append(labels)
                
            #     i += 1
            # inputs = torch.stack(inputs)
            # num_batches = inputs.size()[0]
            # num_input = inputs.size()[2]
            # targets = torch.stack(targets).view(num_batches, num_input)

            # state = self._model.init_hidden(num_batches)

            # outs = []
            # for i in range(batch_size):
            #     input = inputs[:,i,:].view(num_batches, num_input)
            #     out, state = self._model.forward(input, state)
                
            # single_loss = self._loss_function(out, targets)
            # single_loss.backward()
            # self._optimizer.step()

            # ep_loss = single_loss / num_batches
            # print(ep_loss)
            # # print(foo)

            #########################################################################################
            # Update State nach jedem Batch mit End-Prediction, inkl. Teacher Forcing 
            # DISTINCT! but same batches every epoch! 
            # if ep == 0: 

            #     inputs = []
            #     targets = []
            #     batch_size = train_sequence[0][0].size()[0]
            #     for seq, labels in train_sequence:
            #         inputs.append(seq)
            #         targets.append(labels)
                    
            #     inputs = torch.stack(inputs)
            #     num_batches = inputs.size()[0]
            #     batch_length = inputs.size()[1]
            #     num_input = inputs.size()[2]
            #     targets = torch.stack(targets)

            #     print(inputs.shape)
            #     print(targets.shape)
            #     train_loader = DataLoader(
            #         dataset=TensorDataset(inputs, targets),
            #         batch_size=5,
            #         pin_memory=True,
            #         shuffle=True
            #     )

            #     batches_per_epoch = len(train_loader)
            #     print(batches_per_epoch)
                
            #     print(batch_length)

            # for (ins, tars) in train_loader: 
            #     real_num_batches = ins.size()[0]

            #     self._optimizer.zero_grad()

            #     state = self._model.init_hidden(real_num_batches)
            #     outs = []
            #     for i in range(batch_length):
            #         input = ins[:,i,:].view(real_num_batches, num_input)
            #         out, state = self._model.forward(input, state)
            #         # outs.append(out)
            
            #     # outs = torch.stack(outs)
            #     # print(out.shape)
            #     # print(tars.view(real_num_batches, num_input).shape)
            #     single_loss = self._loss_function(out, tars.view(real_num_batches, num_input))
            #     single_loss.backward()
            #     self._optimizer.step()

            #     ep_loss += single_loss
            # print(ep_loss)
            # print(foo)


            #########################################################################################
            # Update State nach jedem Batch mit End-Prediction, inkl. Teacher Forcing 
            # NOT DISTINCT! 
            # for seq, labels in train_sequence:
            #     batch_size = seq.size()[0]
            #     self._optimizer.zero_grad()
            #     state = self._model.init_hidden(1)
            #     for s in seq:
            #         s = s.view(1,45)
            #         y_pred, state = self._model(s, state)
                
            #     single_loss = self._loss_function(y_pred, labels)
            #     single_loss.backward()
            #     self._optimizer.step()

            #     ep_loss += single_loss 

            #########################################################################################
            # Update State nach jedem Batch, kein Teacher Forcing
            # for seq, labels in train_sequence:
            #     batch_size = seq.size()[0]
            #     self._optimizer.zero_grad()
            #     state = self._model.init_hidden(batch_size)
            #     y_pred, state = self._model(seq, state)

            #     # print(foo)
            #     single_loss = self._loss_function(y_pred[-1], labels[0])
            #     single_loss.backward()
            #     self._optimizer.step()

            #     ep_loss += single_loss 
            
            # ep_loss /= num_batches

            # ep_loss /= batches_per_epoch

            # save loss of epoch
            losses.append(ep_loss.item())
            if ep%25 == 1:
                print(f'epoch: {ep:3} loss: {single_loss.item():10.8f}')
        
        print(f'epoch: {ep:3} loss: {single_loss.item():10.10f}')

        self.save_model(save_path)
        self.plot_losses(losses)

        return losses
    

    def plot_losses(self, losses):
        fig = plt.figure()
        axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) 
        axes.plot(losses, 'r')
        axes.grid(True)
        axes.set_xlabel('epochs')
        axes.set_ylabel('loss')
        axes.set_title('History of MSELoss during training')
        plt.show()


    def save_model(self, path):
        torch.save(self._model.state_dict(), path)
        print('Model was saved in: ' + path)



    

def main():
    # LSTM parameters
    frame_samples = 1000
    train_window = 10
    testing_size = 100
    num_features = 15
    num_dimensions = 3

    # Training parameters
    epochs = 2000
    mse=nn.MSELoss()
    # loss_function=nn.MSELoss()
    # loss_function= lambda x, y: mse(x, y) * (num_features * num_dimensions)
    loss_function=nn.L1Loss()
    learning_rate=0.01
    momentum=0.0
    l2_penality=0.1

    # Init tools
    prepro = Preprocessor(num_features, num_features, num_dimensions)
    trainer = LSTM_Trainer(
        loss_function, 
        learning_rate, 
        momentum, 
        l2_penality, 
        train_window
    )
    tester = LSTM_Tester(loss_function)
    tester_1 = LSTM_Tester(mse)

    # Init tools
    data_asf_path = 'Data_Compiler/S35T07.asf'
    data_amc_path = 'Data_Compiler/S35T07.amc'
    model_save_path = 'CoreLSTM/models/LSTM_46_cell_TIMO.pt'

    with torch.no_grad():
        # Preprocess data
        io_seq, dt_train, dt_test = prepro.get_LSTM_data(
            data_asf_path, 
            data_amc_path, 
            frame_samples, 
            testing_size, 
            train_window
        )

    # Train LSTM
    losses = trainer.train(epochs, io_seq, model_save_path)

    test_input = dt_train[0,-train_window:]

    # Test LSTM
    tester.test(testing_size, model_save_path, test_input, dt_test, train_window)
    tester_1.test(testing_size, model_save_path, test_input, dt_test, train_window)
    


if __name__ == "__main__":
    main()


# class LSTMLayer_Trainer():
#     ## General parameters 
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#     def __init__(self, loss_function, learning_rate, momentum):
#         self._model = CORE_NET_Layer()
#         self._loss_function = loss_function
#         self._optimizer = torch.optim.SGD(self._model.parameters(), lr=learning_rate, momentum=momentum)
#         # self._optimizer = torch.optim.SGD(self._model.parameters(), lr=learning_rate)
#         # self._optimizer = torch.optim.Adam(self._model.parameters(), lr=learning_rate)

#         print('Initialized model!')
#         print(self._model)
#         print(self._loss_function)
#         print(self._optimizer)


#     def train(self, epochs, train_sequence, save_path):
#         losses = []

#         for i in range(epochs):
#             for seq, labels in train_sequence:
#                 self._optimizer.zero_grad()

#                 y_pred, state = self._model(seq)

#                 single_loss = self._loss_function(y_pred, labels[0])
#                 single_loss.backward()
#                 self._optimizer.step()

#             # save loss of epoch
#             losses.append(single_loss.item())
#             if i%25 == 1:
#                 print(f'epoch: {i:3} loss: {single_loss.item():10.8f}')
        
#         print(f'epoch: {i:3} loss: {single_loss.item():10.10f}')

#         self.save_model(save_path)
#         self.plot_losses(losses)

#         return losses
    

#     def plot_losses(self, losses):
#         fig = plt.figure()
#         axes = fig.add_axes([0.1, 0.1, 0.8, 0.8]) 
#         axes.plot(losses, 'r')
#         axes.grid(True)
#         axes.set_xlabel('epochs')
#         axes.set_ylabel('loss')
#         axes.set_title('History of MSELoss during training')
#         plt.show()


#     def save_model(self, path):
#         torch.save(self._model.state_dict(), path)
#         print('Model was saved in: ' + path)