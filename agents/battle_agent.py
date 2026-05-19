from collections import deque


class BattleDQNAgent:
  MAX_HAND = 10
  MAX_POTIONS = 10

  ACTION_SET = (
    ["end_turn"]
    + [f"play_card_{card_index}" for card_index in range(MAX_HAND)]
    + [f"use_potion_{slot}" for slot in range(MAX_POTIONS)]
  )

  def __init__(self,
               gamma=0.99,
               epsilon=1.0,
               learning_rate=0.0005,
               epsilon_decay=0.995,
               epsilon_min=0.01,
               batch_size=32,
               memory_size=100000,
               update_freq=4,
               update_freq_target=1000):
    self.action_set = list(self.ACTION_SET)
    self.act2id = {action: i for i, action in enumerate(self.action_set)}
    self.id2act = {i: action for i, action in enumerate(self.action_set)}
    self.id2game_action = {
      action_id: self._action_key_to_game_action(action)
      for action_id, action in self.id2act.items()
    }
    self.action_size = len(self.action_set)

    self.update_freq = update_freq
    self.update_freq_target = update_freq_target

    self.gamma = gamma
    self.epsilon = epsilon
    self.epsilon_decay = epsilon_decay
    self.epsilon_min = epsilon_min
    self.batch_size = batch_size
    self.replay_buffer = deque(maxlen=memory_size)
    self.torch = self._load_torch()
    self.device = (
      self.torch.device("cuda" if self.torch.cuda.is_available() else "cpu")
      if self.torch is not None
      else "cpu"
    )

  def get_action_id(self, action_key: str) -> int:
    return self.act2id[action_key]

  def get_action_key(self, action_id: int) -> str:
    return self.id2act[action_id]

  def get_game_action(self, action_id: int) -> dict:
    return dict(self.id2game_action[action_id])

  def get_game_action_id(self, action: dict) -> int:
    return self.act2id[self._game_action_to_action_key(action)]

  def _action_key_to_game_action(self, action_key: str) -> dict:
    if action_key == "end_turn":
      return {"type": "end_turn"}

    if action_key.startswith("play_card_"):
      return {
        "type": "play_card",
        "card_index": int(action_key.removeprefix("play_card_")),
      }

    if action_key.startswith("use_potion_"):
      return {
        "type": "use_potion",
        "slot": int(action_key.removeprefix("use_potion_")),
      }

    raise ValueError(f"Unknown action key: {action_key}")

  def _game_action_to_action_key(self, action: dict) -> str:
    action_type = action.get("type")

    if action_type == "end_turn":
      return "end_turn"

    if action_type == "play_card":
      return f"play_card_{action['card_index']}"

    if action_type == "use_potion":
      return f"use_potion_{action['slot']}"

    raise ValueError(f"Unknown game action: {action}")

  def _load_torch(self):
    try:
      import torch
    except ModuleNotFoundError:
      return None
    return torch


  def train(self, env, num_episodes, threshold):

    all_rewards = []  # Store rewards for each episode
    total_steps = 0

    
    return all_rewards
