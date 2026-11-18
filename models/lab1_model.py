"""
Вычислительная модель лабораторной работы № 1
«Оценка временных характеристик диалога».

Модуль не зависит от графического интерфейса. Его функции можно вызывать
из Tkinter-приложения, ноутбука или отдельного скрипта.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import numpy as np
import pandas as pd


NORMAL_TOPIC = "Штатная работа"
RECOVERY_TOPIC = "Восстановление"
MAX_ROUTE_STEPS = 10
MAX_ROUTES_PER_TOPIC = 10
REPEAT_STEP = "Повторение текущего шага"
RETURN_TO_PREVIOUS_STEP = "Возврат на предыдущий шаг"
RETURN_TO_DIALOGUE_START = "Возврат в начало диалога"
ERROR_STRATEGIES = (
    REPEAT_STEP,
    RETURN_TO_PREVIOUS_STEP,
    RETURN_TO_DIALOGUE_START,
)


@dataclass(frozen=True)
class Lab1Config:
    """Параметры генерации маршрутов и имитационного эксперимента."""

    n_simulations: int = 10_000
    seed: int = 42
    error_probabilities: tuple[float, ...] = (0.0, 0.3, 0.6, 0.9)
    topic_probabilities: tuple[float, float] = (0.8, 0.2)
    route_counts: tuple[int, int] = (2, 2)
    route_probabilities: tuple[float, ...] = (0.6, 0.4, 0.7, 0.3)
    route_forms: tuple[tuple[str, ...], ...] = ()
    route_times: tuple[tuple[float, ...], ...] = ()
    error_strategy: str = REPEAT_STEP


def validate_config(config: Lab1Config) -> None:
    """Проверяет корректность параметров модели."""

    if config.n_simulations <= 0:
        raise ValueError("Количество имитаций должно быть положительным.")

    if len(config.route_counts) != 2 or any(
        not isinstance(count, int)
        or not 1 <= count <= MAX_ROUTES_PER_TOPIC
        for count in config.route_counts
    ):
        raise ValueError(
            f"Для каждой подтемы нужно задать от 1 до {MAX_ROUTES_PER_TOPIC} маршрутов."
        )

    route_total = sum(config.route_counts)
    if bool(config.route_forms) != bool(config.route_times):
        raise ValueError("Нужно задать обе матрицы: экранные формы и время.")
    if config.route_forms and (
        len(config.route_forms) != route_total
        or len(config.route_times) != route_total
    ):
        raise ValueError("Матрицы форм и времени должны содержать строку для каждого маршрута.")

    for forms, times in zip(config.route_forms, config.route_times):
        if not 1 <= len(forms) <= MAX_ROUTE_STEPS:
            raise ValueError(
                f"В маршруте должно быть от 1 до {MAX_ROUTE_STEPS} экранных форм."
            )
        if len(forms) != len(times):
            raise ValueError(
                "Число экранных форм и времён в строке маршрута должно совпадать."
            )
        if any(not isinstance(form, str) or not form.strip() for form in forms):
            raise ValueError("Название каждой экранной формы не может быть пустым.")
        if any(
            not isinstance(duration, (int, float))
            or not isfinite(duration)
            or duration <= 0
            for duration in times
        ):
            raise ValueError("Время каждой экранной формы должно быть числом больше 0.")

    if config.error_strategy not in ERROR_STRATEGIES:
        raise ValueError("Неизвестная стратегия обработки ошибок.")

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

    if len(config.route_probabilities) != route_total:
        raise ValueError("Для каждого маршрута необходимо задать вероятность.")

    if any(not 0 <= p <= 1 for p in config.route_probabilities):
        raise ValueError("Вероятности маршрутов должны находиться в диапазоне [0, 1].")

    normal_count = config.route_counts[0]
    if not np.isclose(sum(config.route_probabilities[:normal_count]), 1.0):
        raise ValueError("Сумма вероятностей маршрутов штатной работы должна равняться 1.")

    if not np.isclose(sum(config.route_probabilities[normal_count:]), 1.0):
        raise ValueError("Сумма вероятностей маршрутов восстановления должна равняться 1.")


def generate_routes(config: Lab1Config) -> dict[str, list[dict[str, Any]]]:
    """
    Создаёт маршруты из матриц последовательностей экранных форм и времени.
    """

    validate_config(config)

    normal_count, recovery_count = config.route_counts
    default_forms = ("Экран 1", "Экран 2")
    default_times = (2.0, 3.0)
    route_forms = config.route_forms or (default_forms,) * (normal_count + recovery_count)
    route_times = config.route_times or (default_times,) * (normal_count + recovery_count)
    topics = (
        (NORMAL_TOPIC, "A", normal_count, 0),
        (RECOVERY_TOPIC, "B", recovery_count, normal_count),
    )
    routes = {}
    for topic, prefix, count, start_index in topics:
        routes[topic] = [
            {
                "name": f"{prefix}{route_index + 1}",
                "forms": list(route_forms[start_index + route_index]),
                "times": list(route_times[start_index + route_index]),
                "probability": config.route_probabilities[start_index + route_index],
            }
            for route_index in range(count)
        ]
    return routes


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
                "Экранные формы": route["forms"],
                "Время форм, с": route["times"],
                "Количество экранных форм": len(route["forms"]),
                "Вероятность маршрута": route["probability"],
                "Суммарное время маршрута, с": sum(route["times"]),
            })
    return pd.DataFrame(rows)


def simulate_dialogue(
    error_probability: float,
    routes: dict[str, list[dict[str, Any]]],
    topic_probabilities: tuple[float, float] = (0.8, 0.2),
    rng: np.random.Generator | None = None,
    error_strategy: str = REPEAT_STEP,
) -> dict[str, Any]:
    """
    Имитирует одно решение задачи.

    На каждом шаге время прибавляется к общему времени. Если действие
    ошибочное (случайное число меньше Pi), обработка выполняется по выбранной
    стратегии.
    """

    if not 0 <= error_probability < 1:
        raise ValueError("Pi должна находиться в диапазоне [0, 1).")
    if error_strategy not in ERROR_STRATEGIES:
        raise ValueError("Неизвестная стратегия обработки ошибок.")

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

    step_index = 0
    while step_index < len(selected_route["times"]):
        total_time += int(selected_route["times"][step_index])
        if rng.random() >= error_probability:
            step_index += 1
            continue

        total_errors += 1
        if error_strategy == RETURN_TO_PREVIOUS_STEP:
            step_index = max(0, step_index - 1)
        elif error_strategy == RETURN_TO_DIALOGUE_START:
            step_index = 0

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
                error_strategy=config.error_strategy,
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
