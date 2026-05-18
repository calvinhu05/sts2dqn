import torch
import numpy
from collections import deque
class BattleDQNAgent:
  def __init__(self,
               action_set,
               dqn_config,
               gamma,
               epsilon,
               learning_rate=0.0005,
               epsilon_decay=0.995,
               epsilon_min=0.01,
               batch_size=32,
               memory_size=100000,
               update_freq=4,
               update_freq_target=1000):
    self.act2id = {a: i for i, a in enumerate(action_set)}
    self.id2act = {i: a for i, a in enumerate(action_set)}

    self.update_freq = update_freq
    self.update_freq_target = update_freq_target
    self.max_seq_len = 256  # DO NOT CHANGE `max_seq_len`

    self.gamma = gamma
    self.epsilon = epsilon
    self.epsilon_decay = epsilon_decay
    self.epsilon_min = epsilon_min
    self.batch_size = batch_size
    self.replay_buffer = deque(maxlen=memory_size)
    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    


  def train(self, env, num_episodes, threshold):

    all_rewards = []  # Store rewards for each episode
    total_steps = 0

    
    return all_rewards