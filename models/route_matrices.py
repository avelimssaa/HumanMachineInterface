"""Маршруты диалога в формате двух матриц для лабораторной работы №2.

Первая матрица — маршруты по подтемам. Каждая строка описывает один маршрут:
  * столбец 0 — номер подтемы (0 = «Штатная работа», 1 = «Восстановление»);
  * столбец 1 — вероятность выбора этого маршрута;
  * остальные столбцы — номера экранных форм в порядке их прохождения
    (0 означает конец последовательности).

Вторая матрица — время выполнения каждой экранной формы: i-я строка
содержит времена форм подтемы i, j-й элемент строки — время формы с
номером j (форма №0 отсутствует, поэтому первый элемент строки равен 0).

Обе матрицы вводятся текстом: ячейки через запятую, строки с новой строки
(в одну строку можно и через «;»).
"""

from __future__ import annotations

from typing import Any

import numpy as np

MAX_ROUTES_PER_TOPIC = 10
TIME_MATRIX_ROWS = 2  # строка 0 — «Штатная работа», строка 1 — «Восстановление»

DEFAULT_ROUTE_MATRIX = (
    (0, 1.0, 1, 2, 3, 0),
    (0, 0.6, 1, 2, 4, 0),
    (0, 0.4, 3, 4, 0, 0),
    (1, 1.0, 1, 2, 0, 0),
)
DEFAULT_TIME_MATRIX = (
    (0, 3, 4, 2, 5, 6),
    (0, 8, 10, 0, 0, 0),
)


def parse_matrix(raw: str, name: str) -> tuple[tuple[float, ...], ...]:
    """Разбирает текст матрицы: строки с новой строки или через «;», ячейки через «,»."""
    rows: list[tuple[float, ...]] = []
    for line in raw.splitlines():
        text = line.strip().replace(";", ",")
        if not text:
            continue
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if not parts:
            raise ValueError(f"Матрица «{name}» содержит пустую строку.")
        try:
            values = tuple(float(part.replace(",", ".")) for part in parts)
        except ValueError as exc:
            raise ValueError(
                f"Все ячейки матрицы «{name}» должны быть числами."
            ) from exc
        rows.append(values)
    if not rows:
        raise ValueError(f"Матрица «{name}» пуста.")
    return tuple(rows)


def routes_from_matrices(
    route_matrix: tuple[tuple[float, ...], ...],
    time_matrix: tuple[tuple[float, ...], ...],
    topics: tuple[str, str] = ("Штатная работа", "Восстановление"),
) -> dict[str, list[dict[str, Any]]]:
    """Собирает структуру маршрутов из двух матриц.

    Формы нумеруются с 1; 0 и пустые ячейки обозначают конец маршрута.
    Время формы берётся из time_matrix[номер_подтемы][номер_формы].
    """
    if len(time_matrix) != TIME_MATRIX_ROWS:
        raise ValueError(
            "Вторая матрица должна содержать ровно две строки: "
            "времена экранных форм штатной работы и восстановления."
        )
    for row_index, row in enumerate(time_matrix):
        if any(not np.isfinite(value) or value < 0 for value in row):
            raise ValueError(
                f"Времена экранных форм (строка {row_index + 1}) "
                "должны быть неотрицательными числами."
            )

    topic_rows = (
        (topics[0], 0, "A"),
        (topics[1], 1, "B"),
    )
    routes: dict[str, list[dict[str, Any]]] = {}
    for topic, matrix_row, prefix in topic_rows:
        topic_routes: list[dict[str, Any]] = []
        for raw in route_matrix:
            if len(raw) < 3:
                raise ValueError(
                    "В первой матрице каждая строка: номер подтемы, "
                    "вероятность маршрута и хотя бы одна экранная форма."
                )
            if int(round(raw[0])) != matrix_row:
                continue
            probability = float(raw[1])
            if not 0 <= probability <= 1:
                raise ValueError(
                    f"Вероятность маршрута подтемы «{topic}» должна быть в диапазоне [0, 1]."
                )
            forms = [int(form) for form in raw[2:] if int(round(form)) > 0]
            if not forms:
                raise ValueError(
                    f"В маршруте подтемы «{topic}» не указано ни одной экранной формы."
                )
            times = []
            for form in forms:
                if form >= len(time_matrix[matrix_row]):
                    raise ValueError(
                        f"Экранная форма №{form} подтемы «{topic}» отсутствует "
                        f"во второй матрице (в строке {matrix_row + 1} "
                        f"только {len(time_matrix[matrix_row]) - 1} ячеек)."
                    )
                step_time = float(time_matrix[matrix_row][form])
                if step_time <= 0:
                    raise ValueError(
                        f"Время экранной формы №{form} подтемы «{topic}» "
                        "должно быть больше 0."
                    )
                times.append(step_time)
            topic_routes.append(
                {
                    "name": f"{prefix}{len(topic_routes) + 1}",
                    "times": times,
                    "probability": probability,
                }
            )
        if not topic_routes:
            raise ValueError(
                f"В первой матрице нет ни одного маршрута подтемы «{topic}» "
                f"(строки с номером подтемы {matrix_row})."
            )
        if len(topic_routes) > MAX_ROUTES_PER_TOPIC:
            raise ValueError(
                f"Для подтемы «{topic}» нельзя задать больше "
                f"{MAX_ROUTES_PER_TOPIC} маршрутов."
            )
        total = sum(route["probability"] for route in topic_routes)
        if not np.isclose(total, 1.0):
            raise ValueError(
                f"Сумма вероятностей маршрутов подтемы «{topic}» равна {total:g}, "
                "а должна равняться 1."
            )
        routes[topic] = topic_routes
    return routes


def format_matrix(matrix: tuple[tuple[float, ...], ...]) -> str:
    return "\n".join(
        ", ".join(f"{value:g}" for value in row) for row in matrix
    )
