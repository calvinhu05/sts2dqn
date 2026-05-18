import logging
import time
from game import Game
from ai_agent import Agent

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    game = Game(
        state_size=(128,),
        action_size=0,
        character=0,
    )

    agent = Agent()
    episode = 1

    while True:
        state = game.reset()
        done = False
        raw_state = game.client.get_state()

        logging.info("Starting episode %d", episode)

        while raw_state.get("state_type")!="game_over":
            raw_state = game.client.get_state()
            encoded_state = game._encode_state(raw_state)

            policy_state = {
                "screen_type": raw_state.get("state_type"),
                "raw_state": raw_state,
            }

            action = agent.choose_action(policy_state)

            next_state, reward, done, info = game.step(action)

            print(action, reward, done)
            if done:
                break

            time.sleep(0.3)

        logging.info(
            "Episode %d ended; returning to main menu and starting a new run",
            episode,
        )
        episode += 1


if __name__ == "__main__":
    main()
