import logging
import typing as t
import numpy as np
import random

from mcp_api import STS2Client, STS2ClientError, GameCharacter
from player import Player


logger = logging.getLogger(__name__)


class Game:
    """
    Minimal game skeleton for Deep Q-Learning.
    Uses STS2Client as the backend game client.
    """

    def __init__(
        self,
        character: int=0,
        base_url: str = "http://localhost:15526/api/v1",
    ):
        self.character = character
        self.player=Player(character)
        logger.debug("Game: initializing character=%s base_url=%s", character, base_url)

        # Init game client in singleplayer mode
        self.client = STS2Client(
            base_url=base_url,
            mode="singleplayer",
        )

        self._state = self._init_state()

    def reset(self):
        """
        Reset environment and start/create singleplayer mode.

        This tries to move from main menu into:
            menu -> singleplayer -> standard

        Then it returns the current encoded observation.
        """
        raw_state = self.client.get_state()
        logger.debug(
            "Game: reset starting state_type=%s menu_screen=%s",
            raw_state.get("state_type"),
            raw_state.get("menu_screen"),
        )

        if raw_state.get("state_type") == "game_over":
            logger.debug("Game: returning from game_over to main menu")
            self.client.menu_select("main_menu")
            raw_state = self.client.get_state()

        if raw_state.get("state_type") == "menu":
            menu_screen = raw_state.get("menu_screen")

            if menu_screen == "main":
                if "abandon_run" in raw_state.get("options", []):
                    logger.info("Game: abandoning existing run before reset")
                    self.client.menu_select("abandon_run")
                    self.client.menu_select("yes")
                logger.debug("Game: selecting singleplayer menu")
                self.client.menu_select("singleplayer")
                raw_state = self.client.get_state()

            if raw_state.get("state_type") == "menu" and raw_state.get("menu_screen") == "singleplayer":
                logger.debug("Game: selecting standard run")
                self.client.menu_select("standard")
                raw_state = self.client.get_state()
                
            if raw_state.get("state_type") == "menu" and raw_state.get("menu_screen") == "character_select":
                logger.debug("Game: selecting character=%s", self.character)
                self.client.menu_select(GameCharacter.get(self.character, 0))
                self.client.menu_select("confirm")
                raw_state = self.client.get_state()
        self.player=Player(self.character)
        self.act=self.client.get_state().get("run", {}).get("act", 0)
        self.floor=self.client.get_state().get("run", {}).get("floor", 0)
        self.ascension=self.client.get_state().get("run", {}).get("ascension", 0)
        logger.info(
            "Game: started run act=%s floor=%s ascension=%s",
            self.act,
            self.floor,
            self.ascension,
        )
        self._state = self._encode_state(raw_state)


    def _apply_action(self, action: dict, raw_state: dict):
        action_type = action.get("type")
        logger.debug(
            "Game: applying action type=%s state_type=%s action=%s",
            action_type,
            raw_state.get("state_type"),
            action,
        )

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

        logger.warning("Game: unknown action type=%s action=%s", action_type, action)
        raise ValueError(f"Unknown action type: {action_type}")
        
    def is_end_state(self)-> bool:
        return self.client.get_state().get("state_type", False) == "game_over"

    def close(self):
        """Cleanup resources if needed."""
        pass
