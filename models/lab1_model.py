"""
Вычислительная модель лабораторной работы № 1
«Оценка временных характеристик диалога».

Модуль не зависит от графического интерфейса. Его функции можно вызывать
из Tkinter-приложения, ноутбука или отдельного скрипта.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


NORMAL_TOPIC = "Штатная работа"
RECOVERY_TOPIC = "Восстановление"


@dataclass(frozen=True)
class Lab1Config:
    """Параметры генерации маршрутов и имитационного эксперимента."""

    n_simulations: int = 10_000
    seed: int = 42
    min_steps: int = 2
    max_steps: int = 5
    min_step_time: int = 2
    max_step_time: int = 5
    error_probabilities: tuple[float, ...] = (0.0, 0.3, 0.6, 0.9)
    topic_probabilities: tuple[float, float] = (0.8, 0.2)
    route_probabilities: tuple[float, float, float, float] = (
        0.6, 0.4, 0.7, 0.3
    )


def validate_config(config: Lab1Config) -> None:
    """Проверяет корректность параметров модели."""

    if config.n_simulations <= 0:
        raise ValueError("Количество имитаций должно быть положительным.")

    if config.min_steps < 1 or config.min_steps > config.max_steps:
        raise ValueError("Границы количества шагов заданы некорректно.")

    if config.min_step_time < 1 or config.min_step_time > config.max_step_time:
        raise ValueError("Границы времени шага заданы некорректно.")

    if not config.error_probabilities:
        raise ValueError("Нужно задать хотя бы одну вероятность ошибки.")

    if any(not 0 <= p < 1 for p in config.error_probabilities):
        raise ValueError("Вероятности ошибки Pi должны находиться в диапазоне [0, 1).")

    if len(config.topic_probabilities) != 2:
        raise ValueError("Для двух тем необходимо задать две вероятности.")

    if any(not 0 <= p <= 1 for p in config.topic_probabilities):
        raise ValueError("Вероятности выбора тем должны находиться в диапазоне [0, 1].")

    if not np.isclose(sum(config.topic_probabilities), 1.0):
        raise ValueError("Сумма вероятностей выбора тем должна равняться 1.")

    if len(config.route_probabilities) != 4:
        raise ValueError("Необходимо задать вероятности четырёх маршрутов.")

    if any(not 0 <= p <= 1 for p in config.route_probabilities):
        raise ValueError("Вероятности маршрутов должны находиться в диапазоне [0, 1].")

    if not np.isclose(sum(config.route_probabilities[:2]), 1.0):
        raise ValueError("Сумма вероятностей маршрутов A1 и A2 должна равняться 1.")

    if not np.isclose(sum(config.route_probabilities[2:]), 1.0):
        raise ValueError("Сумма вероятностей маршрутов B1 и B2 должна равняться 1.")


def generate_routes(config: Lab1Config) -> dict[str, list[dict[str, Any]]]:
    """
    Генерирует четыре маршрута по правилам исходного ноутбука.

    Для каждого маршрута случайно определяется число шагов, затем
    генерируется время выполнения каждого шага.
    """

    validate_config(config)
    rng = np.random.default_rng(config.seed)

    def generate_steps() -> list[int]:
        n_steps = int(rng.integers(config.min_steps, config.max_steps + 1))
        values = rng.integers(
            config.min_step_time,
            config.max_step_time + 1,
            size=n_steps,
        )
        return [int(value) for value in values]

    p_a1, p_a2, p_b1, p_b2 = config.route_probabilities

    return {
        NORMAL_TOPIC: [
            {"name": "A1", "times": generate_steps(), "probability": p_a1},
            {"name": "A2", "times": generate_steps(), "probability": p_a2},
        ],
        RECOVERY_TOPIC: [
            {"name": "B1", "times": generate_steps(), "probability": p_b1},
            {"name": "B2", "times": generate_steps(), "probability": p_b2},
        ],
    }


def routes_to_dataframe(
    routes: dict[str, list[dict[str, Any]]]
) -> pd.DataFrame:
    """Преобразует описание маршрутов в таблицу для отображения в UI."""

    rows = []
    for topic, topic_routes in routes.items():
        for route in topic_routes:
            rows.append({
                "Подтема": topic,
                "Маршрут": route["name"],
                "Время шагов, с": route["times"],
                "Количество шагов": len(route["times"]),
                "Вероятность маршрута": route["probability"],
                "Суммарное время маршрута, с": sum(route["times"]),
            })
    return pd.DataFrame(rows)


def simulate_dialogue(
    error_probability: float,
    routes: dict[str, list[dict[str, Any]]],
    topic_probabilities: tuple[float, float] = (0.8, 0.2),
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """
    Имитирует одно решение задачи.

    На каждом шаге время прибавляется к общему времени. Если действие
    ошибочное (случайное число меньше Pi), тот же шаг повторяется.
    """

    if not 0 <= error_probability < 1:
        raise ValueError("Pi должна находиться в диапазоне [0, 1).")

    if rng is None:
        rng = np.random.default_rng()

    topics = [NORMAL_TOPIC, RECOVERY_TOPIC]
    topic = str(rng.choice(topics, p=topic_probabilities))
    available_routes = routes[topic]

    route_probabilities = [route["probability"] for route in available_routes]
    route_index = int(rng.choice(len(available_routes), p=route_probabilities))
    selected_route = available_routes[route_index]

    total_time = 0
    total_errors = 0

    for step_time in selected_route["times"]:
        while True:
            total_time += int(step_time)
            if rng.random() >= error_probability:
                break
            total_errors += 1

    return {
        "topic": topic,
        "route": selected_route["name"],
        "time": total_time,
        "errors": total_errors,
    }


def simulate_experiment(
    config: Lab1Config,
    routes: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Выполняет серию экспериментов для всех заданных Pi.

    Возвращает:
      results_df — результаты отдельных имитаций;
      summary_df — статистика по каждому Pi;
      topic_summary_df — статистика по Pi и подтеме.
    """

    validate_config(config)
    if routes is None:
        routes = generate_routes(config)

    rng = np.random.default_rng(config.seed)
    rows: list[dict[str, Any]] = []

    for pi in config.error_probabilities:
        for simulation_number in range(1, config.n_simulations + 1):
            result = simulate_dialogue(
                error_probability=pi,
                routes=routes,
                topic_probabilities=config.topic_probabilities,
                rng=rng,
            )
            rows.append({
                "Pi": pi,
                "simulation": simulation_number,
                "topic": result["topic"],
                "route": result["route"],
                "time": result["time"],
                "errors": result["errors"],
            })

    results_df = pd.DataFrame(rows)

    summary_df = (
        results_df.groupby("Pi")
        .agg(
            Среднее_время=("time", "mean"),
            Медиана=("time", "median"),
            Минимум=("time", "min"),
            Максимум=("time", "max"),
            Стандартное_отклонение=("time", "std"),
        )
        .reset_index()
        .round(2)
    )

    topic_summary_df = (
        results_df.groupby(["Pi", "topic"])
        .agg(
            Число_наблюдений=("time", "count"),
            Среднее_время=("time", "mean"),
            Стандартное_отклонение=("time", "std"),
        )
        .reset_index()
    )
    topic_summary_df[["Среднее_время", "Стандартное_отклонение"]] = (
        topic_summary_df[["Среднее_время", "Стандартное_отклонение"]].round(2)
    )

    return {
        "results_df": results_df,
        "summary_df": summary_df,
        "topic_summary_df": topic_summary_df,
    }


def sturges_bins(sample_size: int) -> int:
    """Возвращает число интервалов по формуле Стерджеса."""

    if sample_size <= 0:
        raise ValueError("Размер выборки должен быть положительным.")
    return max(1, int(1 + 3.22 * np.log10(sample_size)))


def get_histogram_bins(
    sample_size: int,
    bins: int | str | None = None,
) -> int:
    """
    Возвращает число интервалов для гистограммы.

    bins=None или bins='auto' — формула Стерджеса.
    Иначе ожидается положительное целое число.
    """

    if bins is None or bins == "auto":
        return sturges_bins(sample_size)

    try:
        value = int(bins)
    except (TypeError, ValueError) as exc:
        raise ValueError("Количество интервалов должно быть целым числом.") from exc

    if value < 1:
        raise ValueError("Количество интервалов должно быть не меньше 1.")
    return value


def run_lab1(config: Lab1Config) -> dict[str, Any]:
    """Полный запуск ЛР1: генерация маршрутов и моделирование."""

    routes = generate_routes(config)
    experiment = simulate_experiment(config, routes)

    return {
        "routes": routes,
        "routes_df": routes_to_dataframe(routes),
        **experiment,
        "histogram_bins": sturges_bins(config.n_simulations),
    }
