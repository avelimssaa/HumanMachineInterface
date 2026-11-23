"""
HumanMachineInterface — приложение для лабораторных работ №1 и №2.

Запуск:
    python -m pip install -r requirements.txt
    python main.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk as tkttk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.lab1_model import (
    ERROR_STRATEGIES,
    Lab1Config,
    MAX_ROUTE_STEPS,
    MAX_ROUTES_PER_TOPIC,
    get_histogram_bins,
    generate_routes,
    run_lab1,
)
from models.lab2_model import Lab2Config, run_lab2

import json
from tkinter import filedialog

APP_TITLE = "Человеко-машинный интерфейс"
APP_VERSION = "1.2.0"

from utils.UIutils import create_tree, fill_tree, fill_tree_with_pi_separators
from utils.constants import FORMULAS_TEXT

class HumanMachineApp:
    """Главное приложение с вкладками двух лабораторных работ."""

    def __init__(self) -> None:
        self.root = ttk.Window(
            title=f"{APP_TITLE} — Лабораторные работы №1 и №2",
            themename="flatly",
            size=(1320, 860),
            minsize=(1050, 700),
        )
        self.root.place_window_center()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.lab1_result = None
        self.lab2_result = None
        self._configure_style()
        self._build_layout()

    def _configure_style(self) -> None:
        style = self.root.style
        style.configure("AppTitle.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 17, "bold"))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=(22, 18))
        container.pack(fill=BOTH, expand=YES)

        header = ttk.Frame(container)
        header.pack(fill=X, pady=(0, 16))

        title_area = ttk.Frame(header)
        title_area.pack(side=LEFT, fill=X, expand=YES)

        ttk.Label(
            title_area,
            text="Человеко-машинный интерфейс",
            style="AppTitle.TLabel",
        ).pack(anchor=W)

        ttk.Label(
            title_area,
            text="Среда имитационного моделирования · Лабораторные работы №1 и №2",
            style="Subtitle.TLabel",
            bootstyle="secondary",
        ).pack(anchor=W, pady=(3, 0))

        ttk.Label(
            header,
            text=f"Версия {APP_VERSION}",
            bootstyle="secondary",
        ).pack(side=RIGHT, anchor=N, padx=(10, 0))

        self.notebook = ttk.Notebook(container, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES)

        self.lab1_tab = ttk.Frame(self.notebook, padding=16)
        self.lab2_tab = ttk.Frame(self.notebook, padding=16)

        self.notebook.add(self.lab1_tab, text="  Лабораторная №1 · Время диалога  ")
        self.notebook.add(self.lab2_tab, text="  Лабораторная №2 · Эффективность системы  ")

        self._build_lab1_tab()
        self._build_lab2_tab()

        footer = ttk.Frame(container)
        footer.pack(fill=X, pady=(12, 0))
        ttk.Separator(footer).pack(fill=X, pady=(0, 8))

        self.status_var = tk.StringVar(value="Готово к работе")
        ttk.Label(
            footer, textvariable=self.status_var, bootstyle="secondary"
        ).pack(side=LEFT)
        ttk.Label(
            footer, text="Python · Tkinter · Matplotlib", bootstyle="secondary"
        ).pack(side=RIGHT)

    def _build_lab1_tab(self) -> None:
        self.lab1_tab.columnconfigure(0, weight=0, minsize=350)
        self.lab1_tab.columnconfigure(1, weight=1)
        self.lab1_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.lab1_tab)
        left.grid(row=0, column=0, sticky=NSEW, padx=(0, 12))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        parameter_canvas = tk.Canvas(left, highlightthickness=0, width=330)
        parameter_scroll = ttk.Scrollbar(
            left, orient=VERTICAL, command=parameter_canvas.yview
        )
        parameter_canvas.configure(yscrollcommand=parameter_scroll.set)
        parameter_canvas.grid(row=0, column=0, sticky=NSEW)
        parameter_scroll.grid(row=0, column=1, sticky=NS)

        parameters = ttk.Labelframe(
            parameter_canvas,
            text="Параметры моделирования",
            padding=14,
        )
        parameter_window = parameter_canvas.create_window(
            (0, 0), window=parameters, anchor="nw"
        )
        parameters.bind(
            "<Configure>",
            lambda _e: parameter_canvas.configure(
                 scrollregion=parameter_canvas.bbox("all")
            ),
        )
        parameter_canvas.bind(
            "<Configure>",
            lambda e: parameter_canvas.itemconfigure(parameter_window, width=e.width),
        )
        parameters.columnconfigure(0, weight=1)

        results = ttk.Frame(self.lab1_tab)
        results.grid(row=0, column=1, sticky=NSEW)
        results.columnconfigure(0, weight=1)
        results.rowconfigure(2, weight=1)

        ttk.Label(parameters, text="Настройки эксперимента", style="Section.TLabel").grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )

        self.lab1_seed = tk.StringVar(value="42")
        self.lab1_runs = tk.StringVar(value="10000")
        self.lab1_pi_text = tk.StringVar(value="0, 0.3, 0.6, 0.9")
        self.lab1_topic_normal = tk.StringVar(value="0.8")
        self.lab1_topic_recovery = tk.StringVar(value="0.2")
        self.lab1_route_counts = [
            tk.StringVar(value="2"),
            tk.StringVar(value="2"),
        ]
        self.lab1_route_probability_vars = [
            [tk.StringVar(value=value) for value in ("0.6", "0.4") + ("0",) * 8],
            [tk.StringVar(value=value) for value in ("0.7", "0.3") + ("0",) * 8],
        ]

        self.lab1_form_name_vars = [
            tk.StringVar(value=f"Экран {i + 1}" if i < 2 else "")
            for i in range(MAX_ROUTE_STEPS)
        ]
        self.lab1_form_time_vars = [
            tk.StringVar(value=str(i + 2) if i < 2 else "")
            for i in range(MAX_ROUTE_STEPS)
        ]

        self.lab1_route_form_vars = [
                [
                    [
                        tk.StringVar(value=f"Экран {step + 1}" if step < 2 else "")
                        for step in range(MAX_ROUTE_STEPS)
                    ]
                    for _ in range(MAX_ROUTES_PER_TOPIC)
                ]
                for _ in range(2)
            ]
        self.lab1_route_matrix_frames = []
        self.lab1_error_strategy = tk.StringVar(value=ERROR_STRATEGIES[0])
        self.lab1_bins = tk.StringVar(value="")

        row = 1
        fields = [
            ("Начальное значение генератора", self.lab1_seed),
            ("Количество имитаций для каждого Pi", self.lab1_runs),
            ("Вероятности ошибки через запятую", self.lab1_pi_text),
        ]
        for label, variable in fields:
            self._add_entry(parameters, label, variable, row)
            row += 2

        ttk.Label(parameters, text="Стратегия обработки ошибок", style="Section.TLabel").grid(
            row=row, column=0, sticky=W, pady=(8, 4)
        )
        row += 1
        ttk.Combobox(
            parameters,
            textvariable=self.lab1_error_strategy,
            values=ERROR_STRATEGIES,
            state="readonly",
        ).grid(row=row, column=0, sticky=EW)
        row += 1

        ttk.Separator(parameters).grid(row=row, column=0, sticky=EW, pady=12)
        row += 1

        ttk.Label(parameters, text="Количество интервалов гистограммы").grid(
            row=row, column=0, sticky=W, pady=(4, 3)
        )
        row += 1
        ttk.Entry(
            parameters, textvariable=self.lab1_bins,
        ).grid(row=row, column=0, sticky=EW)
        row += 1
        ttk.Label(parameters, text=(
            "Пустое поле или число < 1 — автоматический расчёт по формуле Стерджеса."
        ), wraplength=280, bootstyle="secondary").grid(
            row=row, column=0, sticky=W, pady=(2, 4)
        )
        row += 1

        ttk.Button(parameters, text="Запустить моделирование", bootstyle="success",
                   command=self._run_lab1).grid(row=row, column=0, sticky=EW, ipady=5, pady=(14, 0))
        row += 1
        ttk.Button(parameters, text="Сбросить параметры", bootstyle="secondary-outline",
                   command=self._reset_lab1).grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1

        btn_save = ttk.Button(
            parameters, text="Сохранить конфигурацию", bootstyle="info-outline",
            command=self._save_lab1_config,
        )
        btn_save.grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1
        btn_load = ttk.Button(
            parameters, text="Загрузить конфигурацию", bootstyle="info-outline",
            command=self._load_lab1_config,
        )
        btn_load.grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1

        ttk.Label(parameters, text=(
            "Матрицы маршрутов задаются во вкладке результатов «Матрицы маршрутов». "
            "Стратегия ошибок здесь применяется к моделированию ЛР1."
        ), wraplength=280, bootstyle="secondary").grid(row=row, column=0, sticky=W, pady=(14, 0))

        right = ttk.Frame(self.lab1_tab)
        right.grid(row=0, column=1, sticky=NSEW)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        matrices_frame = ttk.Labelframe(
            right, text="Матрицы маршрутов", padding=8
        )
        matrices_frame.grid(row=0, column=0, sticky=NSEW)
        matrices_frame.columnconfigure(0, weight=1)
        matrices_frame.rowconfigure(0, weight=1)
        self._build_route_matrix_editor(matrices_frame)

        self.lab1_show_results_btn = ttk.Button(
            right,
            text="Показать результаты эксперимента",
            bootstyle="secondary-outline",
            command=self._show_lab1_results,
            state="disabled",
        )
        self.lab1_show_results_btn.grid(row=1, column=0, sticky=EW, pady=(10, 0), ipady=5)

    def _build_lab2_tab(self) -> None:
        self.lab2_tab.columnconfigure(0, weight=0, minsize=330)
        self.lab2_tab.columnconfigure(1, weight=1)
        self.lab2_tab.rowconfigure(0, weight=1)
        self.lab2_topic_normal = tk.StringVar(value="0.8")
        self.lab2_topic_recovery = tk.StringVar(value="0.2")
        self.lab2_route_counts = [tk.StringVar(value="2"), tk.StringVar(value="2")]
        self.lab2_route_probability_vars = [
            [tk.StringVar(value=v) for v in ("0.6", "0.4") + ("0",) * 8],
            [tk.StringVar(value=v) for v in ("0.7", "0.3") + ("0",) * 8],
        ] 
        self.lab2_form_name_vars = [
            tk.StringVar(value=f"Экран {i + 1}" if i < 2 else "")
            for i in range(MAX_ROUTE_STEPS)
        ]
        self.lab2_form_time_vars = [
            tk.StringVar(value=str(i + 2) if i < 2 else "")
            for i in range(MAX_ROUTE_STEPS)
        ] 
        self.lab2_route_form_vars = [
            [
                [
                    tk.StringVar(value=f"Экран {step + 1}" if step < 2 else "")
                    for step in range(MAX_ROUTE_STEPS)
                ]
                for _ in range(MAX_ROUTES_PER_TOPIC)
            ]
            for _ in range(2)
        ]
        self.lab2_route_matrix_frames = []
        left = ttk.Frame(self.lab2_tab)
        left.grid(row=0, column=0, sticky=NSEW, padx=(0, 12))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        parameter_canvas = tk.Canvas(left, highlightthickness=0, width=310)
        parameter_scroll = ttk.Scrollbar(left, orient=VERTICAL, command=parameter_canvas.yview)
        parameter_canvas.configure(yscrollcommand=parameter_scroll.set)
        parameter_canvas.grid(row=0, column=0, sticky=NSEW)
        parameter_scroll.grid(row=0, column=1, sticky=NS)
        parameters = ttk.Labelframe(parameter_canvas, text="Параметры системы", padding=14)
        parameter_window = parameter_canvas.create_window((0, 0), window=parameters, anchor="nw")
        parameters.bind("<Configure>", lambda _e: parameter_canvas.configure(scrollregion=parameter_canvas.bbox("all")))
        parameter_canvas.bind("<Configure>", lambda e: parameter_canvas.itemconfigure(parameter_window, width=e.width))
        parameters.columnconfigure(0, weight=1)

        right = ttk.Frame(self.lab2_tab)
        right.grid(row=0, column=1, sticky=NSEW)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        matrices_frame = ttk.Labelframe(right, text="Матрицы маршрутов ЛР2", padding=8)
        matrices_frame.grid(row=0, column=0, sticky=NSEW)
        matrices_frame.columnconfigure(0, weight=1)
        matrices_frame.rowconfigure(0, weight=1)
        self._build_route_matrix_editor(
            matrices_frame,
            topic_normal_var=self.lab2_topic_normal,
            topic_recovery_var=self.lab2_topic_recovery,
            route_counts=self.lab2_route_counts,
            route_probability_vars=self.lab2_route_probability_vars,
            form_name_vars=self.lab2_form_name_vars,
            form_time_vars=self.lab2_form_time_vars,
            route_form_vars=self.lab2_route_form_vars,
            frames_storage=self.lab2_route_matrix_frames,
            on_count_changed=self._on_lab2_route_count_changed,
        ) 

        self.lab2_show_results_btn = ttk.Button(
            right, text="Показать результаты моделирования",
            bootstyle="secondary-outline",
            command=self._show_lab2_results,
            state="disabled",
        )
        self.lab2_show_results_btn.grid(row=1, column=0, sticky=EW, pady=(10, 0), ipady=5)

        ttk.Label(parameters, text="Параметры имитационного эксперимента", style="Section.TLabel").grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )
        self.lab2_arrival_rate = tk.StringVar(value="0.05")
        self.lab2_failure_mean = tk.StringVar(value="100")
        self.lab2_r1 = tk.StringVar(value="1.0")
        self.lab2_r2 = tk.StringVar(value="5.0")
        self.lab2_duration = tk.StringVar(value="1000")
        self.lab2_runs = tk.StringVar(value="100")
        self.lab2_seed = tk.StringVar(value="42")

        fields = [
            ("Интенсивность поступления заявок, 1/с", self.lab2_arrival_rate),
            ("Средняя наработка на отказ, с", self.lab2_failure_mean),
            ("Удельные потери R1 (задержка)", self.lab2_r1),
            ("Удельные потери R2 (простой)", self.lab2_r2),
            ("Время моделирования, с", self.lab2_duration),
            ("Количество экспериментов", self.lab2_runs),
            ("Начальное значение генератора", self.lab2_seed),
        ]
        row = 1
        for label, variable in fields:
            self._add_entry(parameters, label, variable, row)
            row += 2

        self.lab2_pi_text = tk.StringVar(value="0.1")
        self._add_entry(
            parameters,
            "Вероятности ошибки через запятую",
            self.lab2_pi_text,
            row,
        )
        row += 2

        ttk.Label(parameters, text="Закон времени наработки на отказ").grid(
            row=row, column=0, sticky=W, pady=(8, 4)
        )
        row += 1
        self.lab2_distribution = tk.StringVar(value="Экспоненциальный")
        ttk.Combobox(
            parameters, textvariable=self.lab2_distribution,
            values=("Экспоненциальный", "Равномерный", "Нормальный"),
            state="readonly",
        ).grid(row=row, column=0, sticky=EW)
        row += 1

        ttk.Separator(parameters).grid(row=row, column=0, sticky=EW, pady=12)
        row += 1
        ttk.Button(
            parameters, text="Запустить моделирование", bootstyle="success",
            command=self._run_lab2,
        ).grid(row=row, column=0, sticky=EW, ipady=5)
        row += 1
        ttk.Button(
            parameters, text="Сбросить параметры", bootstyle="secondary-outline",
            command=self._reset_lab2,
        ).grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1

        btn_save = ttk.Button(
            parameters, text="Сохранить конфигурацию", bootstyle="info-outline",
            command=self._save_lab2_config,
        )
        btn_save.grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1

        btn_load = ttk.Button(
            parameters, text="Загрузить конфигурацию", bootstyle="info-outline",
            command=self._load_lab2_config,
        )
        btn_load.grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1

        ttk.Label(
            parameters,
            text=(
                "Модель: один оператор, очередь FIFO и пуассоновский поток заявок. "
                "При отказе текущая и ожидающие заявки аннулируются. Заявки, "
                "поступившие во время восстановления, ожидают его окончания. "
                "Маршруты ЛР2 задаются в матрицах справа; при ошибке повторяется текущий шаг. "
                "Для равномерного закона "
                "используется U(0; 2m), для нормального — N(m; (0,1m)^2). "
            ),
            wraplength=270, bootstyle="secondary", justify=LEFT,
        ).grid(row=row, column=0, sticky=W, pady=(14, 0))

    @staticmethod
    def _add_entry(parent, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=(4, 3))
        ttk.Entry(parent, textvariable=variable).grid(row=row + 1, column=0, sticky=EW)

    def _build_route_matrix_editor(
        self,
        parent,
        *,
        topic_normal_var=None,
        topic_recovery_var=None,
        route_counts=None,
        route_probability_vars=None,
        form_name_vars=None,
        form_time_vars=None,
        route_form_vars=None,
        frames_storage=None,
        on_count_changed=None,
    ) -> None:
        topic_vars = (
            (topic_normal_var or self.lab1_topic_normal),
            (topic_recovery_var or self.lab1_topic_recovery),
        )
        route_counts = route_counts or self.lab1_route_counts
        route_probability_vars = route_probability_vars or self.lab1_route_probability_vars
        form_name_vars = form_name_vars or self.lab1_form_name_vars
        form_time_vars = form_time_vars or self.lab1_form_time_vars
        route_form_vars = route_form_vars or self.lab1_route_form_vars
        frames_storage = frames_storage if frames_storage is not None else self.lab1_route_matrix_frames
        if on_count_changed is None:
            on_count_changed = lambda index: self._on_route_count_changed(index)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        ttk.Label(
            parent,
            text="Справочник экранных форм (общий для всех подтем, форма → время)",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky=W, pady=(0, 2))
        forms_content, forms_canvas = self._create_h_scroll_area(
            parent, row=1, column=0, height=140
        )
        self._render_form_dictionary(
            forms_content, form_name_vars=form_name_vars, form_time_vars=form_time_vars
        )

        topic_notebook = ttk.Notebook(parent)
        topic_notebook.grid(row=2, column=0, sticky=NSEW, pady=(8, 0))
        frames_storage.clear()

        for topic_index, (topic, prefix, topic_var) in enumerate(
            (
                ("Штатная работа", "A", topic_vars[0]),
                ("Восстановление", "B", topic_vars[1]),
            )
        ):
            topic_page = ttk.Frame(topic_notebook, padding=8)
            topic_notebook.add(topic_page, text=topic)
            topic_page.columnconfigure(0, weight=1)
            topic_page.rowconfigure(3, weight=1)

            header = ttk.Frame(topic_page)
            header.grid(row=0, column=0, sticky=EW, pady=(0, 6))
            header.columnconfigure(0, weight=1)
            ttk.Label(
                header, text=f"Подтема «{topic}»", style="Section.TLabel"
            ).grid(row=0, column=0, sticky=W)
            prob = ttk.Frame(header)
            prob.grid(row=1, column=0, sticky=W, pady=(4, 0))
            ttk.Label(prob, text="Вероятность выбора подтемы:").pack(side=LEFT)
            ttk.Entry(prob, textvariable=topic_var, width=10).pack(
                side=LEFT, padx=(6, 0)
            )

            counts = ttk.Frame(topic_page)
            counts.grid(row=1, column=0, sticky=EW, pady=(0, 4))
            ttk.Label(counts, text="Количество маршрутов (1–10):").pack(side=LEFT)
            selector = ttk.Combobox(
                counts,
                textvariable=route_counts[topic_index],
                values=tuple(str(v) for v in range(1, MAX_ROUTES_PER_TOPIC + 1)),
                state="readonly", width=6,
            )
            selector.pack(side=LEFT, padx=(6, 0))
            selector.bind(
                "<<ComboboxSelected>>",
                lambda _e, idx=topic_index: on_count_changed(idx),
            )

            ttk.Label(
                topic_page,
                text="Матрица маршрутов (строки — маршруты, столбцы — шаги)",
                style="Section.TLabel",
            ).grid(row=2, column=0, sticky=W, pady=(8, 2))
            matrix_content, matrix_canvas = self._create_scroll_area(
                topic_page, row=3, column=0, height=280
            )
            frames_storage.append((matrix_content, prefix, matrix_canvas))
            self._render_route_matrices(
                topic_index,
                route_counts=route_counts,
                route_probability_vars=route_probability_vars,
                route_form_vars=route_form_vars,
                frames_storage=frames_storage,
            )

    @staticmethod
    def _create_h_scroll_area(parent, row: int, column: int, height: int = 200):
        wrapper = ttk.Frame(parent)
        wrapper.grid(row=row, column=column, sticky=NSEW)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        canvas = tk.Canvas(wrapper, highlightthickness=0, height=height, background="white")
        h_scroll = ttk.Scrollbar(wrapper, orient=HORIZONTAL, command=canvas.xview)
        canvas.configure(xscrollcommand=h_scroll.set)
        canvas.grid(row=0, column=0, sticky=NSEW)
        h_scroll.grid(row=1, column=0, sticky=EW)
        content = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        return content, canvas

    @staticmethod
    def _create_scroll_area(parent, row: int, column: int, height: int = 200):
        wrapper = ttk.Frame(parent)
        wrapper.grid(row=row, column=column, sticky=NSEW)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            wrapper, highlightthickness=0, height=height, background="white"
        )
        v_scroll = ttk.Scrollbar(wrapper, orient=VERTICAL, command=canvas.yview)
        h_scroll = ttk.Scrollbar(wrapper, orient=HORIZONTAL, command=canvas.xview)
        canvas.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
        )
        canvas.grid(row=0, column=0, sticky=NSEW)
        v_scroll.grid(row=0, column=1, sticky=NS)
        h_scroll.grid(row=1, column=0, sticky=EW)

        content = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.bind(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"),
        )
        canvas.bind(
            "<Shift-MouseWheel>",
            lambda e: canvas.xview_scroll(int(-e.delta / 120), "units"),
        )

        return content, canvas

    def _render_form_dictionary(
        self, frame, *, form_name_vars=None, form_time_vars=None
    ) -> None:
        form_name_vars = form_name_vars or self.lab1_form_name_vars
        form_time_vars = form_time_vars or self.lab1_form_time_vars
        for child in frame.winfo_children():
            child.destroy()

        ttk.Label(frame, text="Экран", style="Section.TLabel").grid(
            row=0, column=0, padx=3, pady=3, sticky=W
        )
        for i in range(MAX_ROUTE_STEPS):
            ttk.Label(frame, text=f"#{i + 1}").grid(
                row=0, column=i + 1, padx=3, pady=3
            )

        ttk.Label(frame, text="Форма").grid(row=1, column=0, padx=3, pady=3, sticky=W)
        for i in range(MAX_ROUTE_STEPS):
            ttk.Entry(
                frame,
                textvariable=form_name_vars[i],
                width=14,
            ).grid(row=1, column=i + 1, padx=3, pady=3)

        ttk.Label(frame, text="Время, с").grid(row=2, column=0, padx=3, pady=3, sticky=W)
        for i in range(MAX_ROUTE_STEPS):
            ttk.Entry(
                frame,
                textvariable=form_time_vars[i],
                width=14,
            ).grid(row=2, column=i + 1, padx=3, pady=3)

    def _render_route_matrices(
        self,
        topic_index: int,
        *,
        route_counts=None,
        route_probability_vars=None,
        route_form_vars=None,
        frames_storage=None,
    ) -> None:
        route_counts = route_counts or self.lab1_route_counts
        route_probability_vars = route_probability_vars or self.lab1_route_probability_vars
        route_form_vars = route_form_vars or self.lab1_route_form_vars
        frames_storage = frames_storage if frames_storage is not None else self.lab1_route_matrix_frames
        matrix_frame, prefix, matrix_canvas = frames_storage[topic_index]
        for child in matrix_frame.winfo_children():
            child.destroy()

        route_count = int(route_counts[topic_index].get())

        ttk.Label(matrix_frame, text="Маршрут", style="Section.TLabel").grid(
            row=0, column=0, padx=3, pady=3, sticky=W
        )
        ttk.Label(matrix_frame, text="P", style="Section.TLabel").grid(
            row=0, column=1, padx=3, pady=3
        )
        for step in range(MAX_ROUTE_STEPS):
            ttk.Label(
                matrix_frame, text=f"Шаг {step + 1}", style="Section.TLabel"
            ).grid(row=0, column=step + 2, padx=3, pady=3)

        for route_index in range(route_count):
            row = route_index + 1
            ttk.Label(
                matrix_frame,
                text=f"{prefix}{route_index + 1}",
                style="Section.TLabel",
            ).grid(row=row, column=0, padx=3, pady=3, sticky=W)

            ttk.Entry(
                matrix_frame,
                textvariable=route_probability_vars[topic_index][route_index],
                width=9,
            ).grid(row=row, column=1, padx=3, pady=3)

            for step in range(MAX_ROUTE_STEPS):
                ttk.Entry(
                    matrix_frame,
                    textvariable=route_form_vars[topic_index][route_index][step],
                    width=14,
                ).grid(row=row, column=step + 2, padx=3, pady=3)

        matrix_frame.update_idletasks()
        matrix_canvas.configure(scrollregion=matrix_canvas.bbox("all"))

    def _on_route_count_changed(self, topic_index: int) -> None:
        route_count = int(self.lab1_route_counts[topic_index].get())
        probability = repr(1 / route_count)
        for variable in self.lab1_route_probability_vars[topic_index][:route_count]:
            variable.set(probability)
        self._render_route_matrices(topic_index)

    def _on_lab2_route_count_changed(self, topic_index: int) -> None:
        route_count = int(self.lab2_route_counts[topic_index].get())
        probability = repr(1 / route_count)
        for variable in self.lab2_route_probability_vars[topic_index][:route_count]:
            variable.set(probability)
        self._render_route_matrices(
            topic_index,
            route_counts=self.lab2_route_counts,
            route_probability_vars=self.lab2_route_probability_vars,
            route_form_vars=self.lab2_route_form_vars,
            frames_storage=self.lab2_route_matrix_frames,
        )

    def _get_lab1_route_data(
        self,
    ) -> tuple[
        tuple[int, int],
        tuple[float, ...],
        tuple[tuple[str, ...], ...],
        tuple[tuple[str, float], ...],
    ]:
        return self._get_route_data(
            self.lab1_route_counts,
            self.lab1_route_probability_vars,
            self.lab1_form_name_vars,
            self.lab1_form_time_vars,
            self.lab1_route_form_vars,
        )

    def _get_lab2_route_data(
        self,
    ) -> tuple[
        tuple[int, int],
        tuple[float, ...],
        tuple[tuple[str, ...], ...],
        tuple[tuple[str, float], ...],
    ]:
        return self._get_route_data(
            self.lab2_route_counts,
            self.lab2_route_probability_vars,
            self.lab2_form_name_vars,
            self.lab2_form_time_vars,
            self.lab2_route_form_vars,
        )

    @staticmethod
    def _get_route_data(
        route_count_vars,
        route_probability_vars,
        form_name_vars,
        form_time_vars,
        route_form_vars,
    ) -> tuple[
        tuple[int, int],
        tuple[float, ...],
        tuple[tuple[str, ...], ...],
        tuple[tuple[str, float], ...],
    ]:
        route_counts = tuple(int(v.get()) for v in route_count_vars)
        form_times_list: list[tuple[str, float]] = []
        for name_var, time_var in zip(form_name_vars, form_time_vars):
            name = name_var.get().strip()
            raw_time = time_var.get().strip()
            if not name and not raw_time:
                continue
            if not name:
                raise ValueError("Укажите имя экранной формы во всех заполненных строках справочника.")
            try:
                duration = float(raw_time)
            except ValueError as exc:
                raise ValueError(f"Время формы «{name}» должно быть числом.") from exc
            if duration <= 0:
                raise ValueError(f"Время формы «{name}» должно быть больше 0.")
            form_times_list.append((name, duration))
        form_times = tuple(form_times_list)

        route_probabilities: list[float] = []
        route_forms: list[tuple[str, ...]] = []
        for topic_index, (count, prefix) in enumerate(zip(route_counts, ("A", "B"))):
            for index in range(count):
                name = f"{prefix}{index + 1}"
                try:
                    probability = float(
                        route_probability_vars[topic_index][index].get()
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"Укажите вероятность выбора маршрута {name}."
                    ) from exc
                route_probabilities.append(probability)

                cells = [
                    var.get().strip()
                    for var in route_form_vars[topic_index][index]
                ]

                last_filled = max(
                    (i for i, v in enumerate(cells) if v), default=-1
                )
                if last_filled < 0:
                    raise ValueError(f"Заполните маршрут {name} экранными формами.")
                forms = cells[: last_filled + 1]
                if any(not v for v in forms):
                    raise ValueError(
                        f"Маршрут {name}: формы нужно заполнять слева направо без пропусков."
                    )
                route_forms.append(tuple(forms))

        return (
            route_counts,
            tuple(route_probabilities),
            tuple(route_forms),
            form_times,
        )

    def _run_lab1(self) -> None:
        try:
            n_simulations = int(self.lab1_runs.get())
            seed = int(self.lab1_seed.get())
            selected_pi = tuple(
                float(x.strip())
                for x in self.lab1_pi_text.get().split(",")
                if x.strip()
            )
            if not selected_pi:
                raise ValueError("Введите хотя бы одну вероятность ошибки Pi через запятую.")
            topic_probabilities = (
                float(self.lab1_topic_normal.get()),
                float(self.lab1_topic_recovery.get()),
            )

            bins_value = self.lab1_bins.get().strip()
            if bins_value:
                try:
                    bins = int(bins_value)
                except ValueError:
                    raise ValueError("Количество интервалов гистограммы должно быть целым числом.")
                if bins < 1:
                    bins = None
            else:
                bins = None

            (
                route_counts,
                route_probabilities,
                route_forms,
                form_times,
            ) = self._get_lab1_route_data()

            config = Lab1Config(
                n_simulations=n_simulations,
                seed=seed,
                error_probabilities=selected_pi,
                topic_probabilities=topic_probabilities,
                route_counts=route_counts,
                route_probabilities=route_probabilities,
                route_forms=route_forms,
                form_times=form_times,
                error_strategy=self.lab1_error_strategy.get(),
            )

            self.status_var.set("Выполняется моделирование лабораторной №1…")
            self.root.update_idletasks()

            result = run_lab1(config)
            self.lab1_result = result
            histogram_bins = get_histogram_bins(n_simulations, bins)

            Lab1ResultsWindow(self.root, result, histogram_bins)
            self.lab1_show_results_btn.configure(state="normal")
            self.status_var.set(
                f"ЛР №1 завершена: {n_simulations} имитаций для каждого Pi; "
                f"всего {len(result['results_df'])} наблюдений."
            )

        except (ValueError, TypeError) as exc:
            messagebox.showerror("Некорректные параметры", str(exc), parent=self.root)
            self.status_var.set("Проверьте параметры лабораторной №1")
        except Exception as exc:
            messagebox.showerror(
                "Ошибка моделирования",
                f"Не удалось выполнить расчёт:\n{exc}",
                parent=self.root,
            )
            self.status_var.set("При моделировании произошла ошибка")

    def _show_lab1_results(self) -> None:
        if self.lab1_result is None:
            return
        try:
            bins_value = self.lab1_bins.get().strip()
            bins = int(bins_value) if bins_value else None
            if bins is not None and bins < 1:
                bins = None
            histogram_bins = get_histogram_bins(
                int(self.lab1_runs.get()), bins
            )
            Lab1ResultsWindow(self.root, self.lab1_result, histogram_bins)
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Некорректные параметры", str(exc), parent=self.root)

    def _get_lab2_pi_values(self) -> tuple[float, ...]:
        text = self.lab2_pi_text.get().strip()
        if not text:
            raise ValueError("Введите хотя бы одну вероятность ошибки Pi через запятую.")
        try:
            values = tuple(float(x.strip()) for x in text.split(",") if x.strip())
        except ValueError as exc:
            raise ValueError(
                "Вероятности ошибки Pi должны быть числами, разделёнными запятой."
            ) from exc
        if not values:
            raise ValueError("Введите хотя бы одну вероятность ошибки Pi через запятую.")
        return values

    def _show_lab2_results(self) -> None:
        if self.lab2_result is not None:
            Lab2ResultsWindow(self.root, self.lab2_result)

    def _run_lab2(self) -> None:
        try:
            config = Lab2Config(
                arrival_rate=float(self.lab2_arrival_rate.get()),
                failure_mean=float(self.lab2_failure_mean.get()),
                r1=float(self.lab2_r1.get()),
                r2=float(self.lab2_r2.get()),
                duration=float(self.lab2_duration.get()),
                n_replications=int(self.lab2_runs.get()),
                error_probabilities=self._get_lab2_pi_values(),
                failure_distribution=self.lab2_distribution.get(),
                seed=int(self.lab2_seed.get()),
            )

            (
                route_counts,
                route_probabilities,
                route_forms,
                form_times,
            ) = self._get_lab2_route_data()

            route_config = Lab1Config(
                n_simulations=1,
                seed=config.seed,
                error_probabilities=(0.0,),
                topic_probabilities=(
                    float(self.lab2_topic_normal.get()),
                    float(self.lab2_topic_recovery.get()),
                ),
                route_counts=route_counts,
                route_probabilities=route_probabilities,
                route_forms=route_forms,
                form_times=form_times,
            )
            routes = generate_routes(route_config)

            self.status_var.set("Выполняется моделирование лабораторной №2…")
            self.root.update_idletasks()
            result = run_lab2(config, routes)
            self.lab2_result = result
            pi_summary = result["pi_summary_df"]
            Lab2ResultsWindow(self.root, result)
            self.lab2_show_results_btn.configure(state="normal")
            self.status_var.set(
                f"ЛР №2 завершена: {len(pi_summary)} значений Pi × "
                f"{config.n_replications} имитационных экспериментов."
            )
        except (ValueError, TypeError, KeyError) as exc:
            messagebox.showerror("Некорректные параметры", str(exc), parent=self.root)
            self.status_var.set("Проверьте параметры лабораторной №2")
        except Exception as exc:
            messagebox.showerror(
                "Ошибка моделирования", f"Не удалось выполнить расчёт:\n{exc}", parent=self.root
            )
            self.status_var.set("При моделировании лабораторной №2 произошла ошибка")

    def _reset_lab1(self) -> None:
        defaults = [
            (self.lab1_seed, "42"),
            (self.lab1_runs, "10000"),
            (self.lab1_pi_text, "0, 0.3, 0.6, 0.9"),
            (self.lab1_topic_normal, "0.8"),
            (self.lab1_topic_recovery, "0.2"),
            (self.lab1_error_strategy, ERROR_STRATEGIES[0]),
            (self.lab1_bins, ""),
        ]
        for variable, value in defaults:
            variable.set(value)

        for i, (name_var, time_var) in enumerate(
            zip(self.lab1_form_name_vars, self.lab1_form_time_vars)
        ):
            if i < 2:
                name_var.set(f"Экран {i + 1}")
                time_var.set(str(i + 2))
            else:
                name_var.set("")
                time_var.set("")

        for variable in self.lab1_route_counts:
            variable.set("2")
        for topic_index, values in enumerate(
            (("0.6", "0.4"), ("0.7", "0.3"))
        ):
            for index, variable in enumerate(
                self.lab1_route_probability_vars[topic_index]
            ):
                variable.set(values[index] if index < len(values) else "0")
    
            for route_index in range(MAX_ROUTES_PER_TOPIC):
                for step in range(MAX_ROUTE_STEPS):
                    var = self.lab1_route_form_vars[topic_index][route_index][step]
                    if route_index < 2 and step < 2:
                        var.set(f"Экран {step + 1}")
                    else:
                        var.set("")
            self._render_route_matrices(topic_index)

        self.lab1_result = None
        self.lab1_show_results_btn.configure(state="disabled")
        self.status_var.set("Параметры лабораторной №1 сброшены")

    def _reset_lab2(self) -> None:
        self.lab2_arrival_rate.set("0.05")
        self.lab2_failure_mean.set("100")
        self.lab2_r1.set("1.0")
        self.lab2_r2.set("5.0")
        self.lab2_duration.set("1000")
        self.lab2_runs.set("100")
        self.lab2_pi_text.set("0.1")
        self.lab2_seed.set("42")
        self.lab2_distribution.set("Экспоненциальный")
        self.lab2_topic_normal.set("0.8")
        self.lab2_topic_recovery.set("0.2")
        for variable in self.lab2_route_counts:
            variable.set("2")
        for topic_index, values in enumerate((("0.6", "0.4"), ("0.7", "0.3"))):
            for index, variable in enumerate(self.lab2_route_probability_vars[topic_index]):
                variable.set(values[index] if index < len(values) else "0")
            for route_index in range(MAX_ROUTES_PER_TOPIC):
                for step in range(MAX_ROUTE_STEPS):
                    variable = self.lab2_route_form_vars[topic_index][route_index][step]
                    variable.set(f"Экран {step + 1}" if route_index < 2 and step < 2 else "")
            self._render_route_matrices(
                topic_index,
                route_counts=self.lab2_route_counts,
                route_probability_vars=self.lab2_route_probability_vars,
                route_form_vars=self.lab2_route_form_vars,
                frames_storage=self.lab2_route_matrix_frames,
            )
        for i, (name_var, time_var) in enumerate(
            zip(self.lab2_form_name_vars, self.lab2_form_time_vars)
        ):
            name_var.set(f"Экран {i + 1}" if i < 2 else "")
            time_var.set(str(i + 2) if i < 2 else "")
        self.lab2_result = None
        self.lab2_show_results_btn.configure(state="disabled")
        self.status_var.set("Параметры лабораторной №2 сброшены")

    def on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    def _collect_lab1_ui_state(self) -> dict:
        """Собирает текущее состояние UI в словарь для сохранения в JSON."""
        return {
            "version": 1,
            "lab1_seed": self.lab1_seed.get(),
            "lab1_runs": self.lab1_runs.get(),
            "lab1_pi_text": self.lab1_pi_text.get(),
            "lab1_topic_normal": self.lab1_topic_normal.get(),
            "lab1_topic_recovery": self.lab1_topic_recovery.get(),
            "lab1_error_strategy": self.lab1_error_strategy.get(),
            "lab1_bins": self.lab1_bins.get(),
            "lab1_route_counts": [var.get() for var in self.lab1_route_counts],
            "lab1_route_probabilities": [
                [var.get() for var in topic_vars]
                for topic_vars in self.lab1_route_probability_vars
            ],
            "lab1_form_names": [var.get() for var in self.lab1_form_name_vars],
            "lab1_form_times": [var.get() for var in self.lab1_form_time_vars],
            "lab1_route_forms": [
                [
                    [var.get() for var in route_vars]
                    for route_vars in topic_vars
                ]
                for topic_vars in self.lab1_route_form_vars
            ],
        }

    def _apply_lab1_ui_state(self, state: dict) -> None:
        """Применяет сохранённое состояние к UI."""
        def set_var(var: tk.StringVar, key: str) -> None:
            if key in state:
                var.set(str(state[key]))

        set_var(self.lab1_seed, "lab1_seed")
        set_var(self.lab1_runs, "lab1_runs")
        set_var(self.lab1_pi_text, "lab1_pi_text")
        set_var(self.lab1_topic_normal, "lab1_topic_normal")
        set_var(self.lab1_topic_recovery, "lab1_topic_recovery")
        set_var(self.lab1_error_strategy, "lab1_error_strategy")
        bins_value = str(state.get("lab1_bins", "")).strip()
        if bins_value in ("Автоматически", "auto", ""):
            bins_value = ""
        self.lab1_bins.set(bins_value)

        for var, value in zip(self.lab1_route_counts, state.get("lab1_route_counts", [])):
            var.set(str(value))

        for topic_vars, saved in zip(
            self.lab1_route_probability_vars,
            state.get("lab1_route_probabilities", []),
        ):
            for var, value in zip(topic_vars, saved):
                var.set(str(value))

        for var, value in zip(self.lab1_form_name_vars, state.get("lab1_form_names", [])):
            var.set(str(value))
        for var, value in zip(self.lab1_form_time_vars, state.get("lab1_form_times", [])):
            var.set(str(value))

        saved_forms = state.get("lab1_route_forms", [])
        for topic_vars, saved_topic in zip(self.lab1_route_form_vars, saved_forms):
            for route_vars, saved_route in zip(topic_vars, saved_topic):
                for var, value in zip(route_vars, saved_route):
                    var.set(str(value))

        for topic_index in range(2):
            self._render_route_matrices(topic_index)


    def _save_lab1_config(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить конфигурацию ЛР1",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        state = self._collect_lab1_ui_state()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self.status_var.set(f"Конфигурация сохранена: {path}")
        except OSError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc), parent=self.root)


    def _load_lab1_config(self) -> None:
        path = filedialog.askopenfilename(
            title="Загрузить конфигурацию ЛР1",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Ошибка загрузки", str(exc), parent=self.root)
            return

        try:
            self._apply_lab1_ui_state(state)
            self.status_var.set(f"Конфигурация загружена: {path}")
        except Exception as exc:
            messagebox.showerror("Ошибка применения", str(exc), parent=self.root)

    def _collect_lab2_ui_state(self) -> dict:
        """Собирает текущее состояние вкладки ЛР2 в словарь для JSON."""
        return {
            "version": 1,
            "lab2_arrival_rate": self.lab2_arrival_rate.get(),
            "lab2_failure_mean": self.lab2_failure_mean.get(),
            "lab2_r1": self.lab2_r1.get(),
            "lab2_r2": self.lab2_r2.get(),
            "lab2_duration": self.lab2_duration.get(),
            "lab2_runs": self.lab2_runs.get(),
            "lab2_seed": self.lab2_seed.get(),
            "lab2_pi_text": self.lab2_pi_text.get(),
            "lab2_distribution": self.lab2_distribution.get(),
        
            "lab2_topic_normal": self.lab2_topic_normal.get(),
            "lab2_topic_recovery": self.lab2_topic_recovery.get(),
            "lab2_route_counts": [var.get() for var in self.lab2_route_counts],
            "lab2_route_probabilities": [
                [var.get() for var in topic_vars]
                for topic_vars in self.lab2_route_probability_vars
            ],
            "lab2_form_names": [var.get() for var in self.lab2_form_name_vars],
            "lab2_form_times": [var.get() for var in self.lab2_form_time_vars],
            "lab2_route_forms": [
                [
                    [var.get() for var in route_vars]
                    for route_vars in topic_vars
                ]
                for topic_vars in self.lab2_route_form_vars
            ],
        }

    def _apply_lab2_ui_state(self, state: dict) -> None:
        """Применяет сохранённое состояние к UI вкладки ЛР2."""
        def set_var(var: tk.StringVar, key: str) -> None:
            if key in state:
                var.set(str(state[key]))

        set_var(self.lab2_arrival_rate, "lab2_arrival_rate")
        set_var(self.lab2_failure_mean, "lab2_failure_mean")
        set_var(self.lab2_r1, "lab2_r1")
        set_var(self.lab2_r2, "lab2_r2")
        set_var(self.lab2_duration, "lab2_duration")
        set_var(self.lab2_runs, "lab2_runs")
        set_var(self.lab2_seed, "lab2_seed")
        set_var(self.lab2_pi_text, "lab2_pi_text")
        set_var(self.lab2_distribution, "lab2_distribution")

        set_var(self.lab2_topic_normal, "lab2_topic_normal")
        set_var(self.lab2_topic_recovery, "lab2_topic_recovery")

        for var, value in zip(self.lab2_route_counts, state.get("lab2_route_counts", [])):
            var.set(str(value))

        for topic_vars, saved in zip(
            self.lab2_route_probability_vars,
            state.get("lab2_route_probabilities", []),
        ):
            for var, value in zip(topic_vars, saved):
                var.set(str(value))

        for var, value in zip(self.lab2_form_name_vars, state.get("lab2_form_names", [])):
            var.set(str(value))
        for var, value in zip(self.lab2_form_time_vars, state.get("lab2_form_times", [])):
            var.set(str(value))

        saved_forms = state.get("lab2_route_forms", [])
        for topic_vars, saved_topic in zip(self.lab2_route_form_vars, saved_forms):
            for route_vars, saved_route in zip(topic_vars, saved_topic):
                for var, value in zip(route_vars, saved_route):
                    var.set(str(value))

        for topic_index in range(2):
            self._render_route_matrices(
                topic_index,
                route_counts=self.lab2_route_counts,
                route_probability_vars=self.lab2_route_probability_vars,
                route_form_vars=self.lab2_route_form_vars,
                frames_storage=self.lab2_route_matrix_frames,
            )


    def _save_lab2_config(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить конфигурацию ЛР2",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            initialfile="lab2_config",
        )
        if not path:
            return
        state = self._collect_lab2_ui_state()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self.status_var.set(f"Конфигурация ЛР2 сохранена: {path}")
        except OSError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc), parent=self.root)

    def _load_lab2_config(self) -> None:
        path = filedialog.askopenfilename(
            title="Загрузить конфигурацию ЛР2",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Ошибка загрузки", str(exc), parent=self.root)
            return

        try:
            self._apply_lab2_ui_state(state)
            self.status_var.set(f"Конфигурация ЛР2 загружена: {path}")
        except Exception as exc:
            messagebox.showerror("Ошибка применения", str(exc), parent=self.root)

class Lab1ResultsWindow(tk.Toplevel):
    """Отдельное окно с результатами ЛР1."""

    def __init__(self, master, result, histogram_bins: int) -> None:
        super().__init__(master)
        self.title("ЛР №1 — Результаты моделирования")
        self.geometry("1280x820")
        self.minsize(1000, 650)
        self.result = result
        self.histogram_bins = histogram_bins

        self._build_metrics_header()
        self._build_notebook()
        self._draw_charts()

    def _build_metrics_header(self) -> None:
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill=X)

        results_df = self.result["results_df"]
        summary_df = self.result["summary_df"]
        topic_df = self.result["topic_summary_df"]

        overall_mean = results_df["time"].mean()
        overall_median = results_df["time"].median()

        metrics = ttk.Frame(header)
        metrics.pack(fill=X)
        for col in range(4):
            metrics.columnconfigure(col, weight=1)

        self._metric_card(metrics, "Эксперименты", f"{len(results_df):,}".replace(",", " "), 0)
        self._metric_card(metrics, "Среднее время решения", f"{overall_mean:.2f} с", 1)
        self._metric_card(metrics, "Медианное время", f"{overall_median:.2f} с", 2)

        normal_mean = topic_df.loc[topic_df["topic"] == "Штатная работа", "Среднее_время"].mean()
        recovery_mean = topic_df.loc[topic_df["topic"] == "Восстановление", "Среднее_время"].mean()
        self._metric_card(
            metrics,
            "Штатная работа / Восстановление",
            f"{normal_mean:.2f} / {recovery_mean:.2f} с",
            3,
        )

    @staticmethod
    def _metric_card(parent, title: str, value: str, column: int):
        card = ttk.Frame(parent, padding=12, bootstyle="light")
        card.grid(row=0, column=column, sticky=EW, padx=(0 if column == 0 else 8, 0))
        ttk.Label(card, text=title, bootstyle="secondary").pack(anchor=W)
        ttk.Label(card, text=value, style="Metric.TLabel").pack(anchor=W, pady=(5, 0))

    def _build_notebook(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=BOTH, expand=YES, padx=16, pady=(0, 16))

        summary_frame = ttk.Frame(notebook, padding=8)
        notebook.add(summary_frame, text="Сводная таблица")
        tree = create_tree(summary_frame)
        fill_tree(tree, self.result["summary_df"])

        topic_frame = ttk.Frame(notebook, padding=8)
        notebook.add(topic_frame, text="По подтемам")
        tree = create_tree(topic_frame)
        fill_tree(tree, self.result["topic_summary_df"])

        routes_frame = ttk.Frame(notebook, padding=8)
        notebook.add(routes_frame, text="Маршруты")
        tree = create_tree(routes_frame)
        fill_tree(tree, self.result["routes_df"])

        charts_frame = ttk.Frame(notebook, padding=8)
        notebook.add(charts_frame, text="Графики")
        self._build_charts_frame(charts_frame)

    def _build_charts_frame(self, parent) -> None:
        
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill=BOTH, expand=YES)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)

        self._plot_view = tk.Canvas(wrapper, highlightthickness=0, background="white")
        vscroll = ttk.Scrollbar(wrapper, orient=VERTICAL, command=self._plot_view.yview)
        hscroll = ttk.Scrollbar(wrapper, orient=HORIZONTAL, command=self._plot_view.xview)
        self._plot_view.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self._plot_view.grid(row=0, column=0, sticky=NSEW)
        vscroll.grid(row=0, column=1, sticky=NS)
        hscroll.grid(row=1, column=0, sticky=EW)

        self._plot_inner = ttk.Frame(self._plot_view)
        self._plot_view.create_window((0, 0), window=self._plot_inner, anchor="nw")
        self._plot_inner.bind(
            "<Configure>",
            lambda _e: self._plot_view.configure(scrollregion=self._plot_view.bbox("all")),
        )
        self._plot_view.bind(
            "<MouseWheel>",
            lambda e: self._plot_view.yview_scroll(int(-e.delta / 120), "units"),
        )

        self._figure = Figure(figsize=(12, 7), dpi=100)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self._plot_inner)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.pack(anchor="nw")

    def _draw_charts(self) -> None:
        results_df = self.result["results_df"]
        summary_df = self.result["summary_df"]
        topic_df = self.result["topic_summary_df"]

        pi_values = sorted(results_df["Pi"].unique())
        n_hist_rows = (len(pi_values) + 1) // 2
        
        total_rows = n_hist_rows + 2

        figure_height = max(9, n_hist_rows * 4.5 + 8.0)
        self._figure.clear()
        self._figure.set_size_inches(12, figure_height, forward=True)
        self._sync_canvas_size()
        grid = self._figure.add_gridspec(
            total_rows, 2,
            height_ratios=[1.0] * n_hist_rows + [1.3, 1.3],
            hspace=0.55, wspace=0.28,
        )

        for index, pi in enumerate(pi_values):
            row = index // 2
            col = index % 2
            ax = self._figure.add_subplot(grid[row, col])
            sample = results_df.loc[results_df["Pi"] == pi, "time"]
            ax.hist(sample, bins=self.histogram_bins, edgecolor="black", alpha=0.75)
            ax.set_title(f"Время диалога при Pi = {pi:g}", fontsize=13, pad=10)
            ax.set_xlabel("Время выполнения, с")
            ax.set_ylabel("Частота")
            ax.grid(axis="y", alpha=0.25)

        ax_mean = self._figure.add_subplot(grid[n_hist_rows, :])
        ax_mean.plot(
            summary_df["Pi"], summary_df["Среднее_время"],
            marker="o", linewidth=2.5, markersize=7,
        )
        ax_mean.set_title(
            "Среднее время решения задачи пользователем в зависимости от Pi",
            fontsize=14, pad=12,
        )
        ax_mean.set_xlabel("Вероятность ошибки Pi")
        ax_mean.set_ylabel("Среднее время, с")
        ax_mean.grid(True, alpha=0.25)

        ax_topics = self._figure.add_subplot(grid[n_hist_rows + 1, :])
        for topic, marker, color in (
            ("Штатная работа", "o", "tab:blue"),
            ("Восстановление", "s", "tab:orange"),
        ):
            subset = topic_df[topic_df["topic"] == topic].sort_values("Pi")
            ax_topics.plot(
                subset["Pi"], subset["Среднее_время"],
                marker=marker, linewidth=2.5, markersize=7,
                label=topic, color=color,
            )
        ax_topics.set_title(
            "Среднее время выполнения каждой подтемы в зависимости от Pi",
            fontsize=14, pad=12,
        )
        ax_topics.set_xlabel("Вероятность ошибки Pi")
        ax_topics.set_ylabel("Среднее время, с")
        ax_topics.grid(True, alpha=0.25)
        ax_topics.legend(loc="best")

        self._figure.subplots_adjust(
            left=0.07, right=0.98, top=0.95, bottom=0.05,
            hspace=0.55, wspace=0.28,
        )

        self._canvas.draw()
        self._plot_inner.update_idletasks()
        w = self._canvas_widget.winfo_reqwidth()
        h = self._canvas_widget.winfo_reqheight()
        self._plot_view.configure(scrollregion=(0, 0, w, h))
        self._plot_view.xview_moveto(0)
        self._plot_view.yview_moveto(0)

    def _sync_canvas_size(self) -> None:
        w = int(self._figure.get_figwidth() * self._figure.dpi)
        h = int(self._figure.get_figheight() * self._figure.dpi)
        self._canvas_widget.configure(width=w, height=h)


class Lab2ResultsWindow(tk.Toplevel):
    """Отдельное окно с результатами ЛР2."""

    def __init__(self, master, result) -> None:
        super().__init__(master)
        self.title("ЛР №2 — Результаты моделирования")
        self.geometry("1280x820")
        self.minsize(1000, 650)
        self.result = result

        self._build_metrics_header()
        self._build_notebook()
        self._draw_charts()

    def _build_metrics_header(self) -> None:
        runs = self.result["runs_df"]
        metrics = ttk.Frame(self, padding=(16, 12))
        metrics.pack(fill=X)
        for column in range(4):
            metrics.columnconfigure(column, weight=1)

        Lab1ResultsWindow._metric_card(
            metrics, "Эксперименты", f"{len(runs):,}".replace(",", " "), 0
        )
        Lab1ResultsWindow._metric_card(
            metrics,
            "Обработано заявок (среднее)",
            f"{runs['Обработано заявок'].mean():.1f}",
            1,
        )
        Lab1ResultsWindow._metric_card(
            metrics,
            "Время простоя (среднее)",
            f"{runs['Время простоя, с'].mean():.2f} с",
            2,
        )
        Lab1ResultsWindow._metric_card(
            metrics,
            "Суммарные потери (среднее)",
            f"{runs['Суммарные потери'].mean():.2f}",
            3,
        )

    def _build_notebook(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=BOTH, expand=YES, padx=16, pady=(0, 16))

        summary_frame = ttk.Frame(notebook, padding=8)
        notebook.add(summary_frame, text="Сводные показатели")
        tree = create_tree(summary_frame)
        fill_tree_with_pi_separators(tree, self.result["summary_df"], pi_column="Pi")

        runs_frame = ttk.Frame(notebook, padding=8)
        notebook.add(runs_frame, text="Эксперименты")
        fill_tree(create_tree(runs_frame), self.result["runs_df"])

        charts_frame = ttk.Frame(notebook, padding=8)
        notebook.add(charts_frame, text="Графики")
        self._figure = Figure(figsize=(11, 7), dpi=100, constrained_layout=True)
        self._canvas = FigureCanvasTkAgg(self._figure, master=charts_frame)
        self._canvas.get_tk_widget().pack(fill=BOTH, expand=YES)

        formulas_frame = ttk.Frame(notebook, padding=8)
        notebook.add(formulas_frame, text="Формулы")
        text = tk.Text(formulas_frame, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        text.pack(fill=BOTH, expand=YES)
        text.insert("1.0", FORMULAS_TEXT)
        text.configure(state="disabled")

    def _draw_charts(self) -> None:
        runs = self.result["runs_df"]
        summary = self.result["pi_summary_df"].sort_values("Pi")
        pi_values = summary["Pi"].to_numpy(dtype=float)

        losses_ax = self._figure.add_subplot(2, 2, (1, 2))
        losses_ax.errorbar(
            pi_values,
            summary["Суммарные потери"].to_numpy(dtype=float),
            yerr=summary["Суммарные потери — Стд. отклонение"].to_numpy(dtype=float),
            marker="o",
            linewidth=2.5,
            capsize=4,
            label="Средние суммарные потери",
        )
        losses_ax.set_title("Зависимость суммарных потерь L от вероятности ошибки Pi")
        losses_ax.set_xlabel("Вероятность ошибки оператора Pi")
        losses_ax.set_ylabel("Суммарные потери L(Pi)")
        losses_ax.grid(True, alpha=0.25)
        losses_ax.legend(loc="best")

        decomposition_ax = self._figure.add_subplot(2, 2, 3)
        decomposition_ax.plot(
            pi_values,
            summary["Потери от задержек"],
            marker="s",
            label="R1 — задержки",
        )
        decomposition_ax.plot(
            pi_values,
            summary["Потери от простоя"],
            marker="^",
            label="R2 — простой",
        )
        decomposition_ax.set_title("Разложение суммарных потерь")
        decomposition_ax.set_xlabel("Pi")
        decomposition_ax.set_ylabel("Потери")
        decomposition_ax.grid(True, alpha=0.25)
        decomposition_ax.legend(loc="best")

        distribution_ax = self._figure.add_subplot(2, 2, 4)
        distribution_ax.hist(
            runs["Суммарные потери"], bins="auto", edgecolor="black", alpha=0.8
        )
        distribution_ax.set_title("Распределение суммарных потерь")
        distribution_ax.set_xlabel("Суммарные потери")
        distribution_ax.set_ylabel("Частота")
        distribution_ax.grid(axis="y", alpha=0.25)

        self._canvas.draw()


if __name__ == "__main__":
    HumanMachineApp().run()

