# -*- coding: utf-8 -*-
"""BayesianOptimization.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ALHkiDt86c_rp5efhK4Nudns5Hc7bGcz
"""

#! pip install ax-platform

#### Biasian Optimization of Deep Neural Hyper Parameters #####
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F

from ax.plot.contour import plot_contour
from ax.plot.trace import optimization_trace_single_method
from ax.service.managed_loop import optimize
from ax.utils.notebook.plotting import render
from ax.utils.tutorials.cnn_utils import train, evaluate

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

import pickle
with open('/content/drive/My Drive/Data/Data.pkl', 'rb') as f:
    df_nve = pickle.load(f)

with open('/content/drive/My Drive/Data/Data_E1_pve.pkl', 'rb') as f:
    df_pve = pickle.load(f)

#Alpha signal
import numpy as np
data_nve = []
for i in range(len(df_nve)):
  data_2_channels = []
  data_2_channels.append(np.array(df_nve[0])[i].transpose()[12])#F3
  data_2_channels.append(np.array(df_nve[0])[i].transpose()[7])#F4
  data_2_channels.append(np.array(df_nve[0])[i].transpose()[11])#F7
  data_2_channels.append(np.array(df_nve[0])[i].transpose()[9])#F8
  #data_2_channels.append(np.array(df_nve[0])[i].transpose()[6])#Fz
  #data_2_channels.append(np.array(df_nve[0])[i].transpose()[14])#T7
  #data_2_channels.append(np.array(df_nve[0])[i].transpose()[3])#T8
  data_nve.append(np.array(data_2_channels).transpose())


data_pve = []
for i in range(len(df_pve)):
  data_2_channels = []
  data_2_channels.append(np.array(df_pve[0])[i].transpose()[12])#F3
  data_2_channels.append(np.array(df_pve[0])[i].transpose()[7])#F4
  data_2_channels.append(np.array(df_pve[0])[i].transpose()[11])#F7
  data_2_channels.append(np.array(df_pve[0])[i].transpose()[9])#F8
  #data_2_channels.append(np.array(df_pve[0])[i].transpose()[6])#Fz
  #data_2_channels.append(np.array(df_pve[0])[i].transpose()[14])#T7
  #data_2_channels.append(np.array(df_pve[0])[i].transpose()[3])#T8
  data_pve.append(np.array(data_2_channels).transpose())

import pandas as pd
df = [df_nve, df_pve]
df = pd.concat(df,ignore_index=True)
print(df)



label_pve = []
for i in range(len(df_pve)):
  label_pve.append(0)
print('pve: ', len(label_pve))


label_nve = []
for i in range(len(df_nve)):
  label_nve.append(1)
print('nve: ', len(label_nve))

labels = label_nve + label_pve
print('label: ',len(labels))

pve_test_points = 40
nve_test_points = 60
#pve_train_points = 
nve_train_points = 300

label_nve_test = label_nve[0:nve_test_points]
print('label_nve_test',len(label_nve_test))
label_pve_test = label_pve[0:pve_test_points]
print('label_pve_test',len(label_pve_test))
df_pve_test =  np.array(data_pve[0:pve_test_points])
print('df_pve_test',len(df_pve_test))
df_nve_test =  np.array(data_nve)[0:nve_test_points]
print('df_nve_test',len(df_nve_test))


label_nve_train = label_nve[nve_test_points:nve_train_points]
print('label_nve_train',len(label_nve_train))
label_pve_train = label_pve[pve_test_points:]
print('label_pve_train',len(label_pve_train))
df_pve_train =  np.array(data_pve)[pve_test_points:]
print('df_pve_train',len(df_pve_train))
df_nve_train =  np.array(data_nve)[nve_test_points:nve_train_points]
print('df_nve_train',len(df_nve_train))

train_data = np.concatenate((df_nve_train, df_pve_train))
print('train_data: ', len(train_data))
train_label = np.concatenate((label_nve_train, label_pve_train))
print('train_label: ', len(train_label))
test_data = np.concatenate((df_nve_test, df_pve_test))
print('test_data: ', len(test_data))
test_label = np.concatenate((label_nve_test, label_pve_test))
print('test_label: ', len(test_label))

from torch.utils.data import Dataset, DataLoader
import numpy as np

class CustomDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, data, label, transform=None):
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.data = data
        self.label = label
        #self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):

        sample_data = self.data[idx]
        sample_label = torch.tensor(np.array(self.label[idx]))
        sample = {'data_point': sample_data, 'label': sample_label}

        if self.transform:
            sample = self.transform(sample)

        return sample

train_dset = CustomDataset(train_data, train_label)
train_loader = DataLoader(train_dset,batch_size=1)
test_dset = CustomDataset(test_data, test_label)
test_loader = DataLoader(test_dset, batch_size = 1)
print(len(train_loader))
print(len(test_loader))

data = next(iter(train_loader))
data_p = data['data_point']
label = data['label']
print(data_p)
print(label)

#### MODEL :- 4 #####

import torch
import torch.nn as nn

class ResBlock(nn.Module):
  def __init__(self, num_ft = 64, kernel_size = 3, stride = 1, padding = 1):
    super(ResBlock, self).__init__()
    m = []
    for _ in range(2):
      m.append(nn.Conv1d(num_ft, num_ft, kernel_size, stride, padding))
      m.append(nn.BatchNorm1d(num_ft))
      m.append(nn.ReLU())
    self.body = nn.Sequential(*m)

  def forward(self, x):
    res = self.body(x)
    res += x
    return res





class ResedualEEGClassifier_3(nn.Module):
  def __init__(self, num_channels,  num_classes, num_res_ft = 64, num_res = 2, input_size = 16,
               hidden_size = 128, sequence_length = 16, num_layers = 1):
    super(ResedualEEGClassifier_3, self).__init__()
    self.conv = nn.Conv1d(num_channels, num_res_ft, kernel_size = 3, stride = 1, padding = 0)
    self.res = ResBlock()
    mat = []
    for _ in range(num_res):
      mat.append(ResBlock(num_ft = num_res_ft))
      mat.append(nn.RReLU())
    self.res_body_1 = nn.Sequential(*mat) 

    self.conv2 = nn.Conv1d(num_res_ft, num_res_ft*2, kernel_size = 3, stride = 1, padding = 0)

    mat2 = []
    for _ in range(num_res):
      mat2.append(ResBlock(num_ft = num_res_ft*2))
      mat2.append(nn.RReLU())
    self.res_body_2 = nn.Sequential(*mat2) 
    self.conv3 = nn.Conv1d(num_res_ft*2, num_res_ft*4, kernel_size = 3, stride = 1, padding = 0)

    mat3 = []
    for _ in range(num_res):
      mat3.append(ResBlock(num_ft = num_res_ft*4))
      mat3.append(nn.RReLU())
    self.res_body_3 = nn.Sequential(*mat3) 
    self.conv4 = nn.Conv1d(num_res_ft*4, num_res_ft*8, kernel_size = 3, stride = 1, padding = 0)

    mat4 = []
    for _ in range(num_res):
      mat4.append(ResBlock(num_ft = num_res_ft*8))
      mat4.append(nn.RReLU())
    self.res_body_4 = nn.Sequential(*mat4) 

    self.avg = nn.AdaptiveAvgPool1d(1)
    self.maxpool = nn.MaxPool1d(1)

    self.fc = nn.Linear(num_res_ft*4, num_classes)
    self.clf = nn.Softmax()

  def forward(self, x):
    x = self.conv(x)
    x = self.res_body_1(x)
    x = self.conv2(x)
    x = self.res_body_2(x)
    x = self.conv3(x)
    x = self.res_body_3(x)
    #x = self.conv4(x)
    #x = self.res_body_4(x)
    x = self.avg(x)
    x = torch.flatten(x)
    x = self.fc(x)
    x = self.clf(x)
    return x

## Training ##
def net_train(net,  parameters, dtype, device,num_channels = 4):
  net.to(dtype=dtype, device=device)

  # Define loss and optimizer
  criterion = nn.CrossEntropyLoss()
  optimizer = optim.Adam(net.parameters(), # or any optimizer you prefer 
                        lr=parameters.get("lr", 0.0001)#, # 0.001 is used if no lr is specified
                        #momentum=parameters.get("momentum", 0.9)
  )

  scheduler = optim.lr_scheduler.StepLR(
      optimizer,
      step_size=int(parameters.get("step_size", 30)),
      gamma=parameters.get("gamma", 1.0),  # default is no learning rate decay
  )

  num_epochs = parameters.get("num_epochs", 100) # Play around with epoch number
  # Train Network
  for epoch in range(num_epochs):
      train_loss = 0.0
      correct = total = 0
      for i in range(len(train_data)):
          # move data to proper dtype and device
          data_point, label = torch.tensor(train_data[i]), torch.tensor(np.array([train_label[i]]))
          data_point, label = data_point.to(device=device), label.to(device=device)
          data_point = data_point.reshape(1,num_channels,-1)

          # zero the parameter gradients
          optimizer.zero_grad()

          # forward + backward + optimize
          output = net(data_point.float())
          loss = criterion(output.reshape(1,-1), label)
          loss.backward()
          optimizer.step()
          scheduler.step()
          train_loss += loss.item()
          _, predicted = torch.max(output.reshape(1,-1).data, 1)
          total += label.size(0)
          correct += (predicted == label).sum().item()
      print('Training Epoch: ', epoch)
      print('training loss: ', train_loss)
      print('Accuracy: ', 100*correct/total)
  return net

def init_net(parameterization):
    num_epoch = 600
    lr = 0.0001
    num_channels = 4
    num_residual_features = 32
    num_resedual_blocks = 5

    model = model = ResedualEEGClassifier_3(num_channels=num_channels, num_res_ft = num_residual_features,
                              num_classes=2, num_layers=2, num_res = num_resedual_blocks)

    # The depth of unfreezing is also a hyperparameter
    #for param in model.parameters():
        #param.requires_grad = False # Freeze feature extractor
        
    #Hs = 512 # Hidden layer size; you can optimize this as well
                                  
    #model.fc = nn.Sequential(nn.Linear(2048, Hs), # attach trainable classifier
                                 #nn.ReLU(),
                                 #nn.Dropout(0.2),
                                 #nn.Linear(Hs, 10),
                                 #nn.LogSoftmax(dim=1))
    return model # return untrained model

def train_evaluate(parameterization):

    # constructing a new training data loader allows us to tune the batch size
    #train_loader = torch.utils.data.DataLoader(trainset,
     #                           batch_size=parameterization.get("batchsize", 32),
      #                          shuffle=True,
       #                         num_workers=0,
        #                        pin_memory=True)
    
    # Get neural net
    untrained_net = init_net(parameterization)
    criterion = nn.CrossEntropyLoss()
    
    # train
    trained_net = net_train(net=untrained_net, 
                            parameters=parameterization, dtype=dtype, device=device)
    
    # return the accuracy of the model as it was trained in this run
    with torch.no_grad():
      val_loss = 0.0
      total = correct = 0
      for j in range(len(test_data)):
        val_data, val_label = torch.tensor(test_data[j]), torch.tensor(np.array([test_label[j]]))
        val_data, val_label = val_data.cuda(), val_label.cuda()
        val_data = val_data.reshape(1,4,-1)
        out_val = trained_net(val_data.float())
        loss = criterion(out_val.reshape(1,-1), val_label)
        val_loss += loss.item()
        _, predicted_val = torch.max(out_val.reshape(1,-1).data, 1)
        total += val_label.size(0)
        correct += (predicted_val == val_label).sum().item()
      acc = correct/total
      print('val_loss: ',val_loss )
      print('val_acc: ', acc)
    return acc

#torch.cuda.set_device(0) #this is sometimes necessary for me
dtype = torch.float
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

best_parameters, values, experiment, model = optimize(
    parameters=[
        {"name": "lr", "type": "range", "bounds": [1e-6, 1e-3], "log_scale": True},
        {"name": "batchsize", "type": "range", "bounds": [16, 128]},
        {"name": "momentum", "type": "range", "bounds": [0.0, 1.0]}
        #{"name": "max_epoch", "type": "range", "bounds": [1, 30]},
        #{"name": "stepsize", "type": "range", "bounds": [20, 40]},        
    ],
  
    evaluation_function=train_evaluate,
    objective_name='accuracy',
)

print(best_parameters)
means, covariances = values
print(means)
print(covariances)
