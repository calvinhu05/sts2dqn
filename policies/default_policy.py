import logging


logger = logging.getLogger(__name__)


class DefaultPolicy:
    def choose_action(self, state: dict) -> dict:
        logger.debug(
            "DefaultPolicy: choosing action state_type=%s",
            state.get("state_type"),
        )
        action = {
            "type": "proceed"
        }
        logger.debug("DefaultPolicy: selected action=%s", action)
        return action
