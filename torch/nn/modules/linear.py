import math

import torch
from torch.nn.parameter import Parameter
from .. import functional as F
from .. import init
from .module import Module
from ..manifolds import create_manifold_parameter


class Linear(Module):
    r"""Applies a linear transformation to the incoming data: :math:`y = xA^T + b`

    Args:
        in_features: size of each input sample
        out_features: size of each output sample
        bias: If set to False, the layer will not learn an additive bias.
            Default: ``True``

    Shape:
        - Input: :math:`(N, *, in\_features)` where :math:`*` means any number of
          additional dimensions
        - Output: :math:`(N, *, out\_features)` where all but the last dimension
          are the same shape as the input.

    Attributes:
        weight: the learnable weights of the module of shape
            `(out_features x in_features)`. The values are initialized from
            :math:`\mathcal{U}(-\sqrt{k}, \sqrt{k})` where
            :math:`k = \frac{1}{\text{in\_features}}`
        bias:   the learnable bias of the module of shape :math:`(out_features)`.
                If :attr:`bias` is ``True``, the values are initialized from
                :math:`\mathcal{U}(-\sqrt{k}, \sqrt{k})` where
                :math:`k = \frac{1}{\text{in\_features}}`

    Examples::

        >>> m = nn.Linear(20, 30)
        >>> input = torch.randn(128, 20)
        >>> output = m(input)
        >>> print(output.size())
    """

    def __init__(self, in_features, out_features, bias=True, weight_manifold=None, transpose_flag=False):
        super(Linear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight_manifold = weight_manifold
        self.transpose_flag = transpose_flag

        if weight_manifold is None:
            self.weight = Parameter(torch.Tensor(out_features, in_features))
        else:
            self.transpose_flag, self.weight = create_manifold_parameter(
                weight_manifold, (out_features, in_features), transpose_flag)

        if bias:
            self.bias = Parameter(torch.Tensor(out_features))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        if self.weight_manifold is None:
            init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        else:
            init.manifold_random_(self.weight)

        if self.bias is not None:
            if self.transpose_flag:
                fan_in, _ = init._calculate_fan_in_and_fan_out(self.weight.transpose(-2, -1))
            else:
                fan_in, _ = init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in)
            init.uniform_(self.bias, -bound, bound)

    def forward(self, input):
        if self.transpose_flag:
            return F.linear(input, self.weight.transpose(-2, -1), self.bias)
        else:
            return F.linear(input, self.weight, self.bias)

    def extra_repr(self):
        return 'in_features={}, out_features={}, bias={}'.format(
            self.in_features, self.out_features, self.bias is not None
        )


class Bilinear(Module):
    r"""Applies a bilinear transformation to the incoming data:
    :math:`y = x_1 A x_2 + b`

    Args:
        in1_features: size of each first input sample
        in2_features: size of each second input sample
        out_features: size of each output sample
        bias: If set to False, the layer will not learn an additive bias.
            Default: ``True``

    Shape:
        - Input: :math:`(N, *, \text{in1\_features})`, :math:`(N, *, \text{in2\_features})`
          where :math:`*` means any number of additional dimensions. All but the last
          dimension of the inputs should be the same.
        - Output: :math:`(N, *, \text{out\_features})` where all but the last dimension
          are the same shape as the input.

    Attributes:
        weight: the learnable weights of the module of shape
            `(out_features x in1_features x in2_features)`. The values are initialized from
            :math:`\mathcal{U}(-\sqrt{k}, \sqrt{k})` where
            :math:`k = \frac{1}{\text{in1\_features}}`
        bias:   the learnable bias of the module of shape `(out_features)`
                If :attr:`bias` is ``True``, the values are initialized from
                :math:`\mathcal{U}(-\sqrt{k}, \sqrt{k})` where
                :math:`k = \frac{1}{\text{in1\_features}}`

    Examples::

        >>> m = nn.Bilinear(20, 30, 40)
        >>> input1 = torch.randn(128, 20)
        >>> input2 = torch.randn(128, 30)
        >>> output = m(input1, input2)
        >>> print(output.size())
    """

    def __init__(self, in1_features, in2_features, out_features, bias=True):
        super(Bilinear, self).__init__()
        self.in1_features = in1_features
        self.in2_features = in2_features
        self.out_features = out_features
        self.weight = Parameter(torch.Tensor(out_features, in1_features, in2_features))

        if bias:
            self.bias = Parameter(torch.Tensor(out_features))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        bound = 1 / math.sqrt(self.weight.size(1))
        init.uniform_(self.weight, -bound, bound)
        if self.bias is not None:
            init.uniform_(self.bias, -bound, bound)

    def forward(self, input1, input2):
        return F.bilinear(input1, input2, self.weight, self.bias)

    def extra_repr(self):
        return 'in1_features={}, in2_features={}, out_features={}, bias={}'.format(
            self.in1_features, self.in2_features, self.out_features, self.bias is not None
        )

# TODO: PartialLinear - maybe in sparse?
