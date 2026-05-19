import typing as t
import numpy as np
import random

from mcp_api import STS2Client, STS2ClientError, GameCharacter
from player import Player

class Game:
    """
    Minimal game skeleton for Deep Q-Learning.
    Uses STS2Client as the backend game client.
    """

    def __init__(
        self,
        character: int=0,
        seed: t.Optional[int] = None,
        base_url: str = "http://localhost:15526/api/v1",
    ):
        self.character = character
        random.seed(seed)
        self.player=Player(character)
        # Init game client in singleplayer mode
        self.client = STS2Client(
            base_url=base_url,
            mode="singleplayer",
        )


    def _init_state(self) -> np.ndarray:
        """Create an initial state. Override for custom state encoding."""
        return np.zeros(self.state_size, dtype=np.float32)

    def _encode_state(self, raw_state: dict) -> np.ndarray:
       '''
       TODO
       '''
       pass

    def reset(self):
        """
        Reset environment and start/create singleplayer mode.

        This tries to move from main menu into:
            menu -> singleplayer -> standard

        Then it returns the current encoded observation.
        """
        raw_state = self.client.get_state()

        if raw_state.get("state_type") == "game_over":
            self.client.menu_select("main_menu")
            raw_state = self.client.get_state()

        if raw_state.get("state_type") == "menu":
            menu_screen = raw_state.get("menu_screen")

            if menu_screen == "main":
                if "abandon_run" in raw_state.get("options", []):
                    self.client.menu_select("abandon_run")
                    self.client.menu_select("yes")
                self.client.menu_select("singleplayer")
                raw_state = self.client.get_state()

            if raw_state.get("state_type") == "menu" and raw_state.get("menu_screen") == "singleplayer":
                self.client.menu_select("standard")
                raw_state = self.client.get_state()
                
            if raw_state.get("state_type") == "menu" and raw_state.get("menu_screen") == "character_select":
                self.client.menu_select(GameCharacter.get(self.character, 0))
                self.client.menu_select("confirm")
                raw_state = self.client.get_state()
        self.player=Player(self.character)
        self.act=self.client.get_state().get("run", {}).get("act", 0)
        self.floor=self.client.get_state().get("run", {}).get("floor", 0)
        self.ascension=self.client.get_state().get("run", {}).get("ascension", 0)
        print(f"Started run: act={self.act}, floor={self.floor}, ascension={self.ascension}")
        self._state = self._encode_state(raw_state)

        return 0

    def step(self, action: dict):
        prev_state = self.client.get_state()

        try:
            api_result = self._apply_action(action, prev_state)
        except Exception as exc:
            raw_state = self.client.get_state()

            reward = -1.0
            done = raw_state.get("state_type") == "game_over"
            info = {
                "error": str(exc),
                "raw_state": raw_state,
                "action": action,
            }

            return 0, reward, done, info

        raw_state = self.client.get_state()

        reward = self._compute_reward(prev_state, raw_state)
        done = raw_state.get("state_type") == "game_over"

        info = {
            "api_result": api_result,
            "raw_state": raw_state,
            "action": action,
        }

        return 0, float(reward), bool(done), info

    def _apply_action(self, action: dict, raw_state: dict):
        action_type = action.get("type")

        if action_type == "end_turn":
            return self.client.end_turn()

        if action_type == "proceed":
            return self.client.proceed()

        if action_type == "play_card":
            return self.client.play_card(
                card_index=action["card_index"],
                target=action.get("target"),
            )

        if action_type == "use_potion":
            return self.client.use_potion(
                slot=action["slot"],
                target=action.get("target"),
            )

        if action_type == "combat_select_card":
            return self.client.combat_select_card(
                card_index=action["card_index"],
            )

        if action_type == "combat_confirm_selection":
            return self.client.combat_confirm_selection()

        if action_type == "choose_map_node":
            return self.client.choose_map_node(
                index=action["index"],
            )

        if action_type == "claim_reward":
            return self.client.claim_reward(
                index=action["index"],
            )

        if action_type == "select_card_reward":
            return self.client.select_card_reward(
                card_index=action["card_index"],
            )

        if action_type == "skip_card_reward":
            return self.client.skip_card_reward()

        if action_type == "choose_rest_option":
            return self.client.choose_rest_option(
                index=action["index"],
            )

        if action_type == "choose_event_option":
            return self.client.choose_event_option(
                index=action["index"],
            )

        if action_type == "advance_dialogue":
            return self.client.advance_dialogue()

        if action_type == "select_card":
            return self.client.select_card(
                index=action["index"],
            )

        if action_type == "confirm_selection":
            return self.client.confirm_selection()

        if action_type == "cancel_selection":
            return self.client.cancel_selection()

        if action_type == "shop_purchase":
            return self.client.shop_purchase(
                index=action["index"],
            )

        raise ValueError(f"Unknown action type: {action_type}")

    def _compute_reward(self, prev_state: dict, next_state: dict) -> float:
        """
        Basic reward function placeholder.

        You should customize this for your RL objective.
        """
        reward = 0.0

        prev_player = prev_state.get("player", {})
        next_player = next_state.get("player", {})

        prev_hp = prev_player.get("hp", 0)
        next_hp = next_player.get("hp", 0)

        prev_floor = prev_state.get("run", {}).get("floor", 0)
        next_floor = next_state.get("run", {}).get("floor", 0)

        # Reward floor progress
        reward += float(next_floor - prev_floor) * 10.0

        # Penalize HP loss
        reward += float(next_hp - prev_hp) * 0.2

        # Terminal reward
        if next_state.get("state_type") == "game_over":
            reward -= 10.0

        return reward

    def sample_action(self) -> int:
        """Sample a random valid action."""
        return int(self.rng.randint(0, self.action_size))

    def render(self, mode: str = "human"):
        """Optional human/array rendering."""
        if mode == "human":
            raw_state = self.client.get_state()
            print("State type:", raw_state.get("state_type"))
            print("Encoded state:", self._state)
        elif mode == "rgb_array":
            return self._state.copy()
        else:
            raise ValueError(f"Unsupported render mode: {mode}")
    def is_end_state(self)-> bool:
        return self.client.get_state().get("state_type", False) == "game_over"

    def close(self):
        """Cleanup resources if needed."""
        pass
