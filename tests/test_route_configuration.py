import unittest

from models.lab1_model import (
    NORMAL_TOPIC,
    REPEAT_STEP,
    RETURN_TO_DIALOGUE_START,
    RETURN_TO_PREVIOUS_STEP,
    Lab1Config,
    generate_routes,
    simulate_dialogue,
    validate_config,
)
from models.lab2_model import _dialogue_time


class ScriptedRng:
    def __init__(self, random_values):
        self.random_values = iter(random_values)

    @staticmethod
    def choice(values, p=None):
        return 0 if isinstance(values, int) else values[0]

    def random(self):
        return next(self.random_values)


class RouteConfigurationTests(unittest.TestCase):
    def test_explicit_route_steps_override_random_generation(self):
        config = Lab1Config(
            route_steps=((1, 3, 5), (2,), (4, 6), (7, 8, 9, 10)),
        )

        routes = generate_routes(config)

        self.assertEqual(routes[NORMAL_TOPIC][0]["times"], [1, 3, 5])
        self.assertEqual(routes[NORMAL_TOPIC][1]["times"], [2])
        self.assertEqual(routes["Восстановление"][0]["times"], [4, 6])
        self.assertEqual(routes["Восстановление"][1]["times"], [7, 8, 9, 10])

    def test_route_with_more_than_ten_steps_is_rejected(self):
        config = Lab1Config(route_steps=((1,) * 11, None, None, None))

        with self.assertRaisesRegex(ValueError, "не может превышать 10|от 1 до 10"):
            validate_config(config)

    def test_route_counts_and_probabilities_are_configurable_per_topic(self):
        config = Lab1Config(
            route_counts=(3, 1),
            route_probabilities=(0.2, 0.3, 0.5, 1.0),
            route_steps=((1,), None, (2, 3), (4,)),
        )

        routes = generate_routes(config)

        self.assertEqual([route["name"] for route in routes[NORMAL_TOPIC]], ["A1", "A2", "A3"])
        self.assertEqual([route["probability"] for route in routes[NORMAL_TOPIC]], [0.2, 0.3, 0.5])
        self.assertEqual([route["name"] for route in routes["Восстановление"]], ["B1"])
        self.assertEqual(routes["Восстановление"][0]["probability"], 1.0)

    def test_ten_routes_per_topic_are_allowed_but_eleven_are_rejected(self):
        config = Lab1Config(
            route_counts=(10, 1),
            route_probabilities=(0.1,) * 10 + (1.0,),
        )

        self.assertEqual(len(generate_routes(config)[NORMAL_TOPIC]), 10)

        invalid_config = Lab1Config(
            route_counts=(11, 1),
            route_probabilities=(1 / 11,) * 11 + (1.0,),
        )
        with self.assertRaisesRegex(ValueError, "от 1 до 10 маршрутов"):
            validate_config(invalid_config)

    def test_route_probabilities_must_sum_to_one_within_each_topic(self):
        config = Lab1Config(
            route_counts=(3, 1),
            route_probabilities=(0.2, 0.3, 0.4, 1.0),
        )

        with self.assertRaisesRegex(ValueError, "штатной работы"):
            validate_config(config)

    def test_return_to_previous_step_repeats_previous_step_after_error(self):
        routes = {
            NORMAL_TOPIC: [{"name": "A1", "times": [10, 20, 30], "probability": 1.0}],
            "Восстановление": [{"name": "B1", "times": [1], "probability": 1.0}],
        }
        rng = ScriptedRng([0.9, 0.1, 0.9, 0.9, 0.9])

        result = simulate_dialogue(
            0.5,
            routes,
            topic_probabilities=(1.0, 0.0),
            rng=rng,
            error_strategy=RETURN_TO_PREVIOUS_STEP,
        )

        self.assertEqual(result["time"], 90)
        self.assertEqual(result["errors"], 1)

    def test_lab2_uses_the_selected_error_strategy(self):
        routes = {
            NORMAL_TOPIC: [{"name": "A1", "times": [10, 20, 30], "probability": 1.0}],
        }
        rng = ScriptedRng([0.9, 0.1, 0.9, 0.9, 0.9])

        total_time = _dialogue_time(
            NORMAL_TOPIC, routes, 0.5, rng, RETURN_TO_PREVIOUS_STEP
        )

        self.assertEqual(total_time, 90)

    def test_return_to_dialogue_start_restarts_route_after_error(self):
        routes = {
            NORMAL_TOPIC: [{"name": "A1", "times": [10, 20, 30], "probability": 1.0}],
            "Восстановление": [{"name": "B1", "times": [1], "probability": 1.0}],
        }
        rng = ScriptedRng([0.9, 0.9, 0.1, 0.9, 0.9, 0.9])

        result = simulate_dialogue(
            0.5,
            routes,
            topic_probabilities=(1.0, 0.0),
            rng=rng,
            error_strategy=RETURN_TO_DIALOGUE_START,
        )

        self.assertEqual(result["time"], 120)
        self.assertEqual(result["errors"], 1)

    def test_lab2_return_to_dialogue_start_restarts_route(self):
        routes = {
            NORMAL_TOPIC: [{"name": "A1", "times": [10, 20, 30], "probability": 1.0}],
        }
        rng = ScriptedRng([0.9, 0.9, 0.1, 0.9, 0.9, 0.9])

        total_time = _dialogue_time(
            NORMAL_TOPIC, routes, 0.5, rng, RETURN_TO_DIALOGUE_START
        )

        self.assertEqual(total_time, 120)

    def test_repeat_strategy_remains_the_default(self):
        self.assertEqual(Lab1Config().error_strategy, REPEAT_STEP)

    def test_repeat_strategy_retries_the_current_step(self):
        routes = {
            NORMAL_TOPIC: [{"name": "A1", "times": [10, 20], "probability": 1.0}],
            "Восстановление": [{"name": "B1", "times": [1], "probability": 1.0}],
        }
        rng = ScriptedRng([0.9, 0.1, 0.9])

        result = simulate_dialogue(
            0.5,
            routes,
            topic_probabilities=(1.0, 0.0),
            rng=rng,
            error_strategy=REPEAT_STEP,
        )

        self.assertEqual(result["time"], 50)
        self.assertEqual(result["errors"], 1)


if __name__ == "__main__":
    unittest.main()
