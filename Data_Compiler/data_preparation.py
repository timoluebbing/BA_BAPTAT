from Data_Compiler.amc_parser import test_all
import torch 

class Preprocessor():
    def __init__(self, num_features, num_dimensions):
        self._num_features = num_features
        self._num_dimensions = num_dimensions


    def compile_data(self, asf_path, amc_path, frame_samples):
        visual_input, selected_joint_names = test_all(asf_path, amc_path, frame_samples, 30) 
        visual_input = torch.from_numpy(visual_input).type(torch.float)

        return visual_input, selected_joint_names
    

    def create_inout_sequences(self, input_data, tw):
        inout_seq = []
        L = len(input_data)
        for i in range(L-tw):
            train_seq = input_data[i:i+tw]
            train_label = input_data[i+tw:i+tw+1]
            inout_seq.append((train_seq ,train_label))
        return inout_seq


    def get_LSTM_data(self, asf_path, amc_path, frame_samples, num_test_data, train_window):
        visual_input, selected_joint_names = self.compile_data(asf_path=asf_path, amc_path=amc_path, frame_samples=frame_samples)

        visual_input = visual_input.permute(1,0,2)
        visual_input = visual_input.reshape(1, frame_samples, self._num_dimensions*self._num_features)

        train_data = visual_input[:,:-num_test_data,:]
        test_data = visual_input[:,-num_test_data:,:]

        train_inout_seq = self.create_inout_sequences(train_data[0], train_window)

        # train_data = train_data.reshape(frame_samples-num_test_data, self._num_features, self._num_dimensions)

        return train_inout_seq, train_data, test_data

    
    def get_AT_data(self, asf_path, amc_path, frame_samples):
        visual_input, selected_joint_names = self.compile_data(asf_path=asf_path, amc_path=amc_path, frame_samples=frame_samples)
        visual_input = visual_input.permute(1,0,2)

        return visual_input, selected_joint_names
    

    def convert_data_AT_to_LSTM(self, data):
        return data.reshape(1, self._num_dimensions*self._num_features)
        # return data.reshape(1, num_samples, self._num_dimensions*self._num_features)


    def convert_data_LSTM_to_AT(self, data): 
        return data.reshape(self._num_features, self._num_dimensions)
        # return data.reshape(num_samples, self._num_features, self._num_dimensions)




