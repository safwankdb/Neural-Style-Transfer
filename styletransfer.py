# -*- coding: utf-8 -*-
"""StyleTransfer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15JKaqmpVNr8NhURJWgbkvIl1sd0aKS3o
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision as tv
from PIL import Image
import imageio
import numpy as np
from matplotlib import pyplot as plt

to_tensor = tv.transforms.Compose([
                tv.transforms.Resize((512,512)),
                tv.transforms.ToTensor(),
                tv.transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[1, 1, 1]),
            ])

unload = tv.transforms.Compose([
                tv.transforms.Normalize(mean=[-0.485,-0.456,-0.406],
                                    std=[1,1,1]),                
                tv.transforms.Lambda(lambda x: x.clamp(0,1))
            ])
to_image = tv.transforms.ToPILImage()

style_img = 'udnie.jpg'
input_img = 'chicago.jpg'

style_img = Image.open(style_img)
input_img = Image.open(input_img)

style_img = to_tensor(style_img).cuda()
input_img = to_tensor(input_img).cuda()

def get_features(module, x, y):
#     print('here')
    features.append(y)
    
def gram_matrix(x):
    
    b, c, h, w = x.size()
    F = x.view(b,c,h*w)
    G = torch.bmm(F, F.transpose(1,2))/(h*w)
    return G

VGG = tv.models.vgg19(pretrained=True).features
VGG.cuda()

for i, layer in enumerate(VGG):
    
    if i in [0,5,10,19,21,28]:
        VGG[i].register_forward_hook(get_features)
    
    elif isinstance(layer, nn.MaxPool2d):
        VGG[i] = nn.AvgPool2d(kernel_size=2)

VGG.eval()

for p in VGG.parameters():
    p.requires_grad = False

features = []
VGG(input_img.unsqueeze(0))
c_target = features[4].detach()

features = []
VGG(style_img.unsqueeze(0))
f_targets = features[:4]+features[5:]
gram_targets = [gram_matrix(i).detach() for i in f_targets]

alpha = 1
beta = 1e3
iterations = 200
image = input_img.clone().unsqueeze(0)
# image = torch.randn(1,3,512,512).cuda()
images = []
optimizer = optim.LBFGS([
image.requires_grad_()], lr=1)    
mse_loss = nn.MSELoss(reduction='mean')
l_c = []
l_s = []
counter = 0

for itr in range(iterations):

    features = []
    def closure():
        optimizer.zero_grad()
        VGG(image)
        t_features = features[-6:]
        content = t_features[4]
        style_features = t_features[:4]+t_features[5:]
        t_features = []
        gram_styles = [gram_matrix(i) for i in style_features]
        c_loss = alpha * mse_loss(content, c_target)
        s_loss = 0

        for i in range(5):
            n_c = gram_styles[i].shape[0]
            s_loss += beta * mse_loss(gram_styles[i],gram_targets[i])/(n_c**2)

        total_loss = c_loss+s_loss

        l_c.append(c_loss)
        l_s.append(s_loss)
        
        total_loss.backward()
        return total_loss

    optimizer.step(closure)
    
    print('Step {}: S_loss: {:.8f} C_loss: {:.8f}'.format(itr, l_s[-1], l_c[-1]))
    

    if itr%1 == 0:
        temp = unload(image[0].cpu().detach())
        temp = to_image(temp)
        temp = np.array(temp)
        images.append(temp)
        imageio.mimsave('progress.gif', images)
        
    
    plt.clf()
    plt.plot(l_c, label='Content Loss')
    plt.legend()
    plt.savefig('loss1.png')
    
    plt.clf()
    plt.plot(l_s, label='Style Loss')
    plt.legend()
    plt.savefig('loss2.png')

plt.imsave('last.jpg',images[-1])

