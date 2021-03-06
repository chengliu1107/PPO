import torch
import gym
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torchviz import make_dot
from torch.distributions import Categorical
from torch.distributions import MultivariateNormal
# agent
class policy_network(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(policy_network, self).__init__()
        self.actor = nn.Sequential(
            nn.Linear(state_dim, action_dim),
            nn.Softmax(dim=-1)
            )
        
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 2),
            nn.ReLU(),
            nn.Linear(2, 1)
            )
    
        self.mseLoss = nn.MSELoss()

    def forward(self, x):
        return self.actor(x)

# env and policy initialization
env = gym.make("LunarLander-v2")
state_dim = env.observation_space.shape[0]
action_dim = 4
policy = policy_network(state_dim, action_dim)

state_np = env.reset()
state =torch.from_numpy(state_np)

# optimizer
optimizer = optim.Adam(params=policy.parameters(), lr=0.001)

# generate distribution
action_prob = policy(state)
# if the action_prob is not generated by the policy network, there will be no error when calculating \
# the loss backward, but there will be grad acculumated on actor parameters.
#action_prob = torch.tensor([0.1, 0.2, 0.3, 0.4])
dist = Categorical(action_prob)

# execute action and get rewards
action = dist.sample()
next_state, reward, done, _ = env.step(action.item())
log_prob = dist.log_prob(action)
dist_entropy = dist.entropy()
state_value = policy.critic(state).view(-1)

print('probabilities generated by policy network:', action_prob, '\n')
print('sampled action and its log probability:', action, log_prob, '\n')

# handcrafted loss function
# why reshape reward? UserWarning: Using a target size (torch.Size([])) that \
# is different to the input size (torch.Size([1])). This will likely lead to \
# incorrect results due to broadcasting. Please ensure they have the same size.
# return F.mse_loss(input, target, reduction=self.reduction)

loss = -log_prob - dist_entropy + policy.mseLoss(state_value, torch.tensor(reward).reshape(-1))

loss.backward()
# for _, params in policy.named_parameters():
#     print(_, params.grad)

# visualization of calculation graph
# visual_graph = make_dot(loss, params=dict(policy.named_parameters()))
# visual_graph.view()

# how sample() and rsample() func are different?
torch.manual_seed(123)
a = torch.zeros(4, requires_grad=True)
b = torch.eye(4, requires_grad=True)
dist = MultivariateNormal(a, b)
#action = dist.sample()
#action = dist.rsample().detach()
action = dist.rsample()
log_prob = dist.log_prob(action)
loss = torch.exp(log_prob)

loss.backward()
print(a.grad, b.grad)