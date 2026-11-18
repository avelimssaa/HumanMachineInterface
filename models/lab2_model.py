"""Имитационная модель лабораторной работы №2.

Модель использует маршруты диалога из lab1_model. Система имеет одного
оператора (один канал обслуживания), входящий поток заявок является пуассоновским,
а отказы образуют поток с выбранным законом времени наработки на отказ.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .lab1_model import (
    ERROR_STRATEGIES,
    NORMAL_TOPIC,
    RECOVERY_TOPIC,
    REPEAT_STEP,
    RETURN_TO_DIALOGUE_START,
    RETURN_TO_PREVIOUS_STEP,
)


@dataclass(frozen=True)
class Lab2Config:
    arrival_rate: float = 1.0
    failure_mean: float = 100.0
    r1: float = 1.0
    r2: float = 5.0
    duration: float = 1000.0
    n_replications: int = 100
    error_probabilities: tuple[float, ...] = (0.1,)
    failure_distribution: str = "Экспоненциальный"
    seed: int = 42
    error_strategy: str = REPEAT_STEP


def validate_lab2_config(config: Lab2Config) -> None:
    if config.arrival_rate <= 0:
        raise ValueError("Интенсивность поступления заявок должна быть больше 0.")
    if config.failure_mean <= 0:
        raise ValueError("Средняя наработка на отказ должна быть больше 0.")
    if config.r1 < 0 or config.r2 < 0:
        raise ValueError("Удельные потери R1 и R2 не могут быть отрицательными.")
    if config.duration <= 0:
        raise ValueError("Время моделирования должно быть больше 0.")
    if config.n_replications <= 0:
        raise ValueError("Количество экспериментов должно быть больше 0.")
    if not config.error_probabilities:
        raise ValueError("Должна быть задана хотя бы одна вероятность ошибки Pi.")
    if any(not 0 <= p < 1 for p in config.error_probabilities):
        raise ValueError("Вероятности ошибки Pi должны находиться в диапазоне [0, 1).")
    if config.failure_distribution not in ("Экспоненциальный", "Равномерный", "Нормальный"):
        raise ValueError("Неизвестный закон распределения времени наработки на отказ.")
    if config.error_strategy not in ERROR_STRATEGIES:
        raise ValueError("Неизвестная стратегия обработки ошибок.")


def _sample_failure_interval(config: Lab2Config, rng: np.random.Generator) -> float:
    """Генерирует положительный интервал между отказами.

    Для равномерного закона используется U(0, 2m), для нормального —
    N(m, (0.1m)^2) с повторной генерацией отрицательных значений.
    """
    mean = config.failure_mean
    if config.failure_distribution == "Экспоненциальный":
        value = rng.exponential(mean)
    elif config.failure_distribution == "Равномерный":
        value = rng.uniform(0.0, 2.0 * mean)
    else:
        value = rng.normal(mean, 0.1 * mean)
        while value <= 0:
            value = rng.normal(mean, 0.1 * mean)
    return max(float(value), 1e-9)


def _dialogue_time(
    topic: str,
    routes: dict[str, list[dict[str, Any]]],
    error_probability: float,
    rng: np.random.Generator,
    error_strategy: str,
) -> float:
    """Время прохождения маршрута с выбранной стратегией обработки ошибок."""
    available = routes[topic]
    probabilities = np.asarray([route["probability"] for route in available], dtype=float)
    probabilities = probabilities / probabilities.sum()
    route = available[int(rng.choice(len(available), p=probabilities))]
    total = 0.0
    step_index = 0
    while step_index < len(route["times"]):
        total += float(route["times"][step_index])
        if rng.random() >= error_probability:
            step_index += 1
        elif error_strategy == RETURN_TO_PREVIOUS_STEP:
            step_index = max(0, step_index - 1)
        elif error_strategy == RETURN_TO_DIALOGUE_START:
            step_index = 0
    return total


def _simulate_one(
    config: Lab2Config,
    routes: dict[str, list[dict[str, Any]]],
    rng: np.random.Generator,
    error_probability: float,
) -> dict[str, float | int]:
    """Одна событийная имитация работы системы на интервале [0, T]."""
    t = 0.0
    horizon = config.duration
    next_arrival = float(rng.exponential(1.0 / config.arrival_rate))
    next_failure = _sample_failure_interval(config, rng)
    repair_end = float("inf")
    downtime_started = None
    downtime = 0.0
    is_up = True

    queue: list[float] = []  # времена поступления ожидающих заявок
    active_arrival: float | None = None
    service_end = float("inf")

    arrivals = completed = cancelled = failures = 0
    total_delay = 0.0

    def start_next_service(now: float) -> None:
        nonlocal active_arrival, service_end
        if is_up and active_arrival is None and queue:
            active_arrival = queue.pop(0)
            service_time = _dialogue_time(
                NORMAL_TOPIC, routes, error_probability, rng,
                config.error_strategy,
            )
            service_end = now + service_time

    while True:
        candidates = {"arrival": next_arrival}
        if is_up:
            candidates["failure"] = next_failure
            candidates["completion"] = service_end
        else:
            candidates["repair"] = repair_end

        event, event_time = min(candidates.items(), key=lambda item: item[1])
        if event_time > horizon:
            break
        t = event_time

        if event == "arrival":
            arrivals += 1
            queue.append(t)
            next_arrival = t + float(rng.exponential(1.0 / config.arrival_rate))
            start_next_service(t)

        elif event == "completion":
            completed += 1
            if active_arrival is not None:
                total_delay += t - active_arrival
            active_arrival = None
            service_end = float("inf")
            start_next_service(t)

        elif event == "failure":
            failures += 1
            is_up = False
            downtime_started = t
            # По условию ЛР2 все ожидающие и обрабатываемая заявки задачи 1
            # аннулируются в момент отказа.
            if active_arrival is not None:
                total_delay += t - active_arrival
                cancelled += 1
            for arrival_time in queue:
                total_delay += t - arrival_time
                cancelled += 1
            active_arrival = None
            service_end = float("inf")
            queue.clear()

            recovery_time = _dialogue_time(
                RECOVERY_TOPIC, routes, error_probability, rng,
                config.error_strategy,
            )
            repair_end = t + recovery_time
            next_failure = float("inf")

        elif event == "repair":
            if downtime_started is not None:
                downtime += t - downtime_started
            downtime_started = None
            repair_end = float("inf")
            is_up = True
            next_failure = t + _sample_failure_interval(config, rng)
            start_next_service(t)

    # Учитываем простой, незавершённый диалог и очередь на момент окончания опыта.
    if not is_up and downtime_started is not None:
        downtime += horizon - downtime_started
    if active_arrival is not None:
        total_delay += horizon - active_arrival
    for arrival_time in queue:
        total_delay += horizon - arrival_time

    delay_losses = config.r1 * total_delay
    downtime_losses = config.r2 * downtime
    total_losses = delay_losses + downtime_losses
    mean_delay = total_delay / arrivals if arrivals else 0.0
    pending = (1 if active_arrival is not None else 0) + len(queue)

    return {
        "Поступило заявок": arrivals,
        "Обработано заявок": completed,
        "Аннулировано заявок": cancelled,
        "Ожидает завершения": pending,
        "Количество отказов": failures,
        "Время простоя, с": downtime,
        "Доступность, %": 100.0 * (horizon - downtime) / horizon,
        "Средняя задержка, с": mean_delay,
        "Потери от задержек": delay_losses,
        "Потери от простоя": downtime_losses,
        "Суммарные потери": total_losses,
        "Потери на заявку": total_losses / arrivals if arrivals else 0.0,
    }


def run_lab2(
    config: Lab2Config,
    routes: dict[str, list[dict[str, Any]]],
) -> dict[str, pd.DataFrame]:
    """Выполняет серию независимых имитаций для каждой заданной Pi.

    Возвращает:
      runs_df — результаты отдельных прогонов (со столбцом «Pi»);
      summary_df — сводная статистика по каждому показателю и каждой Pi;
      pi_summary_df — средние значения ключевых показателей по Pi
        (используется для графиков L(Pi) и разложения потерь на R1/R2).
    """
    validate_lab2_config(config)
    for topic in (NORMAL_TOPIC, RECOVERY_TOPIC):
        if topic not in routes or not routes[topic]:
            raise ValueError(f"Не заданы маршруты для подтемы «{topic}».")
        if any(not route.get("times") for route in routes[topic]):
            raise ValueError(f"В маршрутах подтемы «{topic}» должны быть шаги.")

    rng = np.random.default_rng(config.seed)
    rows = []
    for pi in sorted(set(float(p) for p in config.error_probabilities)):
        for replication in range(1, config.n_replications + 1):
            row = _simulate_one(config, routes, rng, pi)
            row["Эксперимент"] = replication
            row["Pi"] = pi
            rows.append(row)

    runs_df = pd.DataFrame(rows)
    metric_columns = [
        column for column in runs_df.columns
        if column not in ("Эксперимент", "Pi")
    ]

    summary_rows = []
    for pi, group in runs_df.groupby("Pi"):
        for column in metric_columns:
            summary_rows.append({
                "Pi": pi,
                "Показатель": column,
                "Среднее значение": group[column].mean(),
                "Стандартное отклонение": group[column].std(ddof=1) if len(group) > 1 else 0.0,
            })
    summary_df = pd.DataFrame(summary_rows).round(3)

    key_metrics = (
        "Потери от задержек",
        "Потери от простоя",
        "Суммарные потери",
        "Время простоя, с",
        "Средняя задержка, с",
        "Доступность, %",
        "Обработано заявок",
        "Аннулировано заявок",
        "Количество отказов",
        "Потери на заявку",
    )
    grouped = runs_df.groupby("Pi")
    mean_df = grouped[list(key_metrics)].mean().reset_index()
    std_df = grouped[list(key_metrics)].std(ddof=1).fillna(0.0).reset_index()
    std_df.columns = [
        "Pi" if column == "Pi" else f"{column} — Стд. отклонение"
        for column in std_df.columns
    ]
    pi_summary_df = mean_df.merge(std_df, on="Pi").round(3)

    return {
        "runs_df": runs_df.round(3),
        "summary_df": summary_df,
        "pi_summary_df": pi_summary_df,
    }
