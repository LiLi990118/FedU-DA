import torch.nn as nn
import torch
import numpy as np
import torch
from torch.distributions.uniform import Uniform
#################################
# Models for federated learning #
#################################
# McMahan et al., 2016; 199,210 parameters
class TwoNN(nn.Module):
    def __init__(self, name, in_features, num_hiddens, num_classes):
        super(TwoNN, self).__init__()
        self.name = name
        self.activation = nn.ReLU(True)

        self.fc1 = nn.Linear(in_features=in_features, out_features=num_hiddens, bias=True)
        self.fc2 = nn.Linear(in_features=num_hiddens, out_features=num_hiddens, bias=True)
        self.fc3 = nn.Linear(in_features=num_hiddens, out_features=num_classes, bias=True)

    def forward(self, x):
        if x.ndim == 4:
            x = x.view(x.size(0), -1)
        x = self.activation(self.fc1(x))
        x = self.activation(self.fc2(x))
        x = self.fc3(x)
        return x

# McMahan et al., 2016; 1,663,370 parameters
class CNN(nn.Module):
    def __init__(self, name, in_channels, hidden_channels, num_hiddens, num_classes):
        super(CNN, self).__init__()
        self.name = name
        self.activation = nn.ReLU(True)

        self.conv1 = nn.Conv2d(in_channels=in_channels, out_channels=hidden_channels, kernel_size=(5, 5), padding=1, stride=1, bias=False)
        self.conv2 = nn.Conv2d(in_channels=hidden_channels, out_channels=hidden_channels * 2, kernel_size=(5, 5), padding=1, stride=1, bias=False)

        self.maxpool1 = nn.MaxPool2d(kernel_size=(2, 2), padding=1)
        self.maxpool2 = nn.MaxPool2d(kernel_size=(2, 2), padding=1)
        self.flatten = nn.Flatten()

        self.fc1 = nn.Linear(in_features=(hidden_channels * 2) * (7 * 7), out_features=num_hiddens, bias=False)
        self.fc2 = nn.Linear(in_features=num_hiddens, out_features=num_classes, bias=False)

    def forward(self, x):
        x = self.activation(self.conv1(x))
        x = self.maxpool1(x)

        x = self.activation(self.conv2(x))
        x = self.maxpool2(x)
        x = self.flatten(x)

        x = self.activation(self.fc1(x))
        x = self.fc2(x)
        return x

# for CIFAR10
class CNN2(nn.Module):
    def __init__(self, name, in_channels, hidden_channels, num_hiddens, num_classes):
        super(CNN2, self).__init__()
        self.name = name
        self.activation = nn.ReLU(True)

        self.conv1 = nn.Conv2d(in_channels=in_channels, out_channels=hidden_channels, kernel_size=(5, 5), padding=1, stride=1, bias=False)
        self.conv2 = nn.Conv2d(in_channels=hidden_channels, out_channels=hidden_channels * 2, kernel_size=(5, 5), padding=1, stride=1, bias=False)

        self.maxpool1 = nn.MaxPool2d(kernel_size=(2, 2), padding=1)
        self.maxpool2 = nn.MaxPool2d(kernel_size=(2, 2), padding=1)
        self.flatten = nn.Flatten()

        self.fc1 = nn.Linear(in_features=(hidden_channels * 2) * (8 * 8), out_features=num_hiddens, bias=False)
        self.fc2 = nn.Linear(in_features=num_hiddens, out_features=num_classes, bias=False)

    def forward(self, x):
        x = self.activation(self.conv1(x))
        x = self.maxpool1(x)

        x = self.activation(self.conv2(x))
        x = self.maxpool2(x)
        x = self.flatten(x)

        x = self.activation(self.fc1(x))
        x = self.fc2(x)

        return x

def get_activation(activation_type):
    activation_type = activation_type.lower()
    if hasattr(nn, activation_type):
        return getattr(nn, activation_type)()
    else:
        return nn.ReLU()

def _make_nConv(in_channels, out_channels, nb_Conv, activation='ReLU'):
    layers = []
    layers.append(ConvBatchNorm(in_channels, out_channels, activation))

    for _ in range(nb_Conv - 1):
        layers.append(ConvBatchNorm(out_channels, out_channels, activation))
    return nn.Sequential(*layers)

class ConvBatchNorm(nn.Module):
    """(convolution => [BN] => ReLU)"""

    def __init__(self, in_channels, out_channels, activation='ReLU'):
        super(ConvBatchNorm, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels,
                              kernel_size=3, padding=1)
        self.norm = nn.BatchNorm2d(out_channels)
        self.activation = get_activation(activation)

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = self.activation(out)
        return out
class ConvB(nn.Module):
    """(convolution => [BN] => ReLU)"""

    def __init__(self, in_channels, out_channels, activation='ReLU'):
        super(ConvB, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels,
                              kernel_size=3, padding=1)
        self.norm = nn.BatchNorm2d(out_channels)
        self.activation = get_activation(activation)
        self.conv2 = nn.Conv2d(out_channels, out_channels,
                              kernel_size=3, padding=1)
        self.norm2 = nn.BatchNorm2d(out_channels)
        self.activation2 = get_activation(activation)

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        out = self.activation(out)
        out = self.conv2(out)
        out = self.norm2(out)
        out = self.activation2(out)
        return out

class DownBlock(nn.Module):
    """Downscaling with maxpool convolution"""

    def __init__(self, in_channels, out_channels, nb_Conv, activation='ReLU'):
        super(DownBlock, self).__init__()
        self.maxpool = nn.MaxPool2d(2)
        self.nConvs = _make_nConv(in_channels, out_channels, nb_Conv, activation)

    def forward(self, x):
        out = self.maxpool(x)
        return self.nConvs(out)
class SKConv(nn.Module):
    def __init__(self, features, WH, M, G, r, stride=1, L=32):
        """ Constructor
        Args:
            features: input channel dimensionality.
            WH: input spatial dimensionality, used for GAP kernel size.
            M: the number of branchs.
            G: num of convolution groups.
            r: the radio for compute d, the length of z.
            stride: stride, default 1.
            L: the minimum dim of the vector z in paper, default 32.
        """
        super(SKConv, self).__init__()
        d = max(int(features / r), L)
        self.M = M
        self.features = features
        self.convs = nn.ModuleList([])
        for i in range(M):
            self.convs.append(nn.Sequential(
                nn.Conv2d(features, features, kernel_size=3 + i * 2, stride=stride, padding=1 + i, groups=G),
                nn.BatchNorm2d(features),
                nn.LeakyReLU()
            ))
        # self.gap = nn.AvgPool2d(int(WH/stride))
        self.fc = nn.Linear(features, d)
        self.fcs = nn.ModuleList([])
        for i in range(M):
            self.fcs.append(
                nn.Linear(d, features)
            )
        self.softmax = nn.Softmax(dim=1)
        # self.channel_att = ChannelAttention(features, reduction_ratio=16)
        # self.spatial_att = SpatialAttention(kernel_size=7)

    def forward(self, x):
        for i, conv in enumerate(self.convs):
            fea = conv(x).unsqueeze_(dim=1)
            if i == 0:
                feas = fea
            else:
                feas = torch.cat([feas, fea], dim=1)

        fea_U = torch.sum(feas, dim=1)
        fea_s = fea_U.mean(-1).mean(-1)
        fea_z = self.fc(fea_s)
        for i, fc in enumerate(self.fcs):
            vector = fc(fea_z).unsqueeze_(dim=1)
            if i == 0:
                attention_vectors = vector
            else:
                attention_vectors = torch.cat([attention_vectors, vector], dim=1)
        attention_vectors = self.softmax(attention_vectors)
        attention_vectors = attention_vectors.unsqueeze(-1).unsqueeze(-1)
        fea_v = (feas * attention_vectors).sum(dim=1)
        return fea_v
class UpBlock(nn.Module):
    """Upscaling then conv"""

    def __init__(self, in_channels, out_channels, nb_Conv, activation='ReLU'):
        super(UpBlock, self).__init__()

        # self.up = nn.Upsample(scale_factor=2)
        #..................................................................................
        self.up = nn.ConvTranspose2d(in_channels,in_channels//2,(2,2),2)
        self.nConvs = _make_nConv(in_channels, in_channels//2, nb_Conv, activation)
        self.sk = SKConv(features=in_channels, WH=32, M=2, G=8, r=2)

    def forward(self, x, skip_x):
        out = self.up(x)
        x = torch.cat([out, skip_x], dim=1)  # dim 1 is the channel dimension
        x = self.sk(x)
        return self.nConvs(x)


class DynamicConv2d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, padding=1):
        super(DynamicConv2d, self).__init__()
        self.num_branches = 5
        self.branches = nn.ModuleList()
        for i in range(self.num_branches):
            self.branches.append(nn.Sequential(
                nn.Conv2d(in_channels//5, out_channels//5, kernel_size=1),
                nn.BatchNorm2d(out_channels//5),
                nn.ReLU(),
                nn.Conv2d(out_channels//5, out_channels//5, kernel_size=kernel_size,padding=1),
                nn.BatchNorm2d(out_channels//5),
                nn.ReLU()
            ))

    def forward(self, x):
        # split the input tensor into 5 parts along the channel dimension
        x_split = torch.chunk(x, self.num_branches, dim=1)
        # apply different convolutions to each part
        out = []
        for i in range(self.num_branches):
            out.append(self.branches[i](x_split[i]))
        # concatenate the outputs from the different branches along the channel dimension
        out = torch.cat(out, dim=1)
        return out

class UNet(nn.Module):
    def __init__(self,name, in_channels, num_classes):
        '''
        n_channels : number of channels of the input.
                        By default 3, because we have RGB images
        n_labels : number of channels of the ouput.
                      By default 3 (2 labels + 1 for the background)
        '''
        super().__init__()
        self.n_channels = in_channels
        self.n_classes = num_classes
        self.name = name
        # Question here
        n_channels = 32
        self.inc = ConvB(in_channels, n_channels)
        self.down1 = DownBlock(n_channels, n_channels*2, nb_Conv=2)
        self.down2 = DownBlock(n_channels*2, n_channels*4, nb_Conv=2)
        self.down3 = DownBlock(n_channels*4, n_channels*8, nb_Conv=2)
        self.down4 = DownBlock(n_channels*8, n_channels*16, nb_Conv=2)
        self.up4 = UpBlock(n_channels*16, n_channels*4, nb_Conv=2)
        self.up3 = UpBlock(n_channels*8, n_channels*2, nb_Conv=2)
        self.up2 = UpBlock(n_channels*4, n_channels, nb_Conv=2)
        self.up1 = UpBlock(n_channels*2, n_channels, nb_Conv=2)
        self.outc = nn.Conv2d(n_channels, num_classes, kernel_size=(1,1))
        #self.DynamicConv2d = DynamicConv2d(num_classes,num_classes)
        if num_classes == 1:
            self.last_activation = nn.Sigmoid()
        else:
            self.last_activation = None

    #     self.cls = nn.Sequential(
    #         nn.Dropout(p=0.5),  # p为不保留节点数的比例。
    #         nn.Conv2d(n_channels*16, 5, 1),  # Conv2d的参数：输入的特征通道，卷积核尺寸，步长
    #         nn.AdaptiveMaxPool2d(1),  # 自适应最大池化，参数为（H,W）或只有一个H，表示输出信号的尺寸。输出的尺寸不变，后两个维度变为参数大小。
    #         nn.Softmax())
    #
    # def dotProduct(self, seg, cls):
    #     B, N, H, W = seg.size()  # seg是传入的深度卷积结果，是矩阵。
    #     seg = seg.view(B, N, H * W)  # view和reshape作用一样，重新定义矩阵的性状。
    #     final = torch.einsum("ijk,ij->ijk", [seg, cls])  # 利用爱因斯坦求和约定方法求乘积的和。
    #     final = final.view(B, N, H, W)
    #     return final



    def forward(self, x):
        # Question here
        x = x.float()
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        #cls_branch = self.cls(x5).squeeze(3).squeeze(2)
        # (B,N,1,1)->(B,N)  #操作(dropout, conv1*1, adaptiveMaxPool, Sigmoid)后，产生一个二维张量  squeeze(x)只有当维度x的值为1时，才能去掉该维度。
        #cls_branch_max = cls_branch.argmax(dim=1)
        # dim=1将1维去掉，返回最大值对应的索引。  通过argmax，分类结果被转为一个单一数字输出。  #argmax(a, axis=None, out=Nont):a为输入的数组；axis=0按列寻找，axis=1按行寻找最大值对应的索引；out结果将被插入到a中。
        #cls_branch_max = cls_branch_max[:, np.newaxis].float()  # 在np.newaxis的位置增加一个维度，故此时是增加一个列维度。

        x = self.up4(x5, x4)
        x = self.up3(x, x3)
        x = self.up2(x, x2)
        x = self.up1(x, x1)

        if self.last_activation is not None:
            logits = self.last_activation(self.outc(x))
            # print("111")
        else:
            logits = self.outc(x)
        #logits = self.dotProduct(logits, cls_branch)
            # print("222")
        # logits = self.outc(x) # if using BCEWithLogitsLoss
        # print(logits.size())
        #logits = self.DynamicConv2d(logits)
        return logits


if __name__ == '__main__':
    print('#### Test Case ###')
    from torch.autograd import Variable
    x = Variable(torch.rand(2,1,224,224)).cuda()
    model = UNet('unet',1,5).cuda()
    #param = count_param(model)
    y = model(x)
    print('Output shape:',y.shape)
    #print('UNet totoal parameters: %.2fM (%d)'%(param/1e6,param))
    param1 = sum([param.nelement() for param in model.parameters()])
    # param = count_param(model)
    y = model(x)
    # print('UNet totoal parameters: %.2fM (%d)'%(param/1e6,param))
    print(param1)