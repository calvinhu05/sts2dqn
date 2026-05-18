import logging

from policies.battle_policy import BattlePolicy
from policies.map_policy import MapPolicy
from policies.reward_policy import RewardPolicy
from policies.shop_policy import ShopPolicy
from policies.rest_policy import RestPolicy
from policies.event_policy import EventPolicy
from policies.default_policy import DefaultPolicy


logger = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        self.battle_policy = BattlePolicy()
        self.map_policy = MapPolicy()
        self.reward_policy = RewardPolicy()
        self.shop_policy = ShopPolicy()
        self.rest_policy = RestPolicy()
        self.event_policy = EventPolicy()
        self.default_policy = DefaultPolicy()

    def choose_action(self, state: dict) -> dict:
        screen_type = state.get("screen_type")
        raw_state = state["raw_state"]

        logger.debug("Agent: choosing action screen_type=%s", screen_type)

        if screen_type in ["monster", "elite", "boss", "hand_select"]:
            action = self.battle_policy.choose_action(raw_state)
            logger.debug("Agent: selected BattlePolicy action=%s", action)
            return action

        if screen_type == "map":
            action = self.map_policy.choose_action(raw_state)
            logger.debug("Agent: selected MapPolicy action=%s", action)
            return action

        if screen_type in ["rewards", "card_reward"]:
            action = self.reward_policy.choose_action(raw_state)
            logger.debug("Agent: selected RewardPolicy action=%s", action)
            return action

        if screen_type == "shop":
            action = self.shop_policy.choose_action(raw_state)
            logger.debug("Agent: selected ShopPolicy action=%s", action)
            return action

        if screen_type in ["rest", "rest_site"]:
            action = self.rest_policy.choose_action(raw_state)
            logger.debug("Agent: selected RestPolicy action=%s", action)
            return action

        if screen_type in ["event", "card_select"]:
            action = self.event_policy.choose_action(raw_state)
            logger.debug("Agent: selected EventPolicy action=%s", action)
            return action

        action = self.default_policy.choose_action(raw_state)
        logger.debug("Agent: selected DefaultPolicy action=%s", action)
        return action
