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
    get_histogram_bins,
    generate_routes,
    run_lab1,
)
from models.lab2_model import Lab2Config, run_lab2


APP_TITLE = "Человеко-машинный интерфейс"
APP_VERSION = "0.4.0"


class HumanMachineApp:
    """Главное приложение с вкладками двух лабораторных работ."""

    LAB2_PI_CHOICES = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)

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

        # Левая панель прокручивается: все параметры эксперимента доступны
        # даже при небольшом разрешении экрана.
        left = ttk.Frame(self.lab1_tab)
        left.grid(row=0, column=0, sticky=NSEW, padx=(0, 12))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        parameter_canvas = tk.Canvas(left, highlightthickness=0, width=330)
        parameter_scroll = ttk.Scrollbar(left, orient=VERTICAL, command=parameter_canvas.yview)
        parameter_canvas.configure(yscrollcommand=parameter_scroll.set)
        parameter_canvas.grid(row=0, column=0, sticky=NSEW)
        parameter_scroll.grid(row=0, column=1, sticky=NS)
        parameters = ttk.Labelframe(parameter_canvas, text="Параметры моделирования", padding=14)
        parameter_window = parameter_canvas.create_window((0, 0), window=parameters, anchor="nw")
        parameters.bind("<Configure>", lambda _e: parameter_canvas.configure(scrollregion=parameter_canvas.bbox("all")))
        parameter_canvas.bind("<Configure>", lambda e: parameter_canvas.itemconfigure(parameter_window, width=e.width))
        parameter_canvas.bind_all("<MouseWheel>", lambda e: parameter_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        parameters.columnconfigure(0, weight=1)

        results = ttk.Frame(self.lab1_tab)
        results.grid(row=0, column=1, sticky=NSEW)
        results.columnconfigure(0, weight=1)
        results.rowconfigure(2, weight=1)

        ttk.Label(parameters, text="Настройки эксперимента", style="Section.TLabel").grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )

        self.lab1_seed = tk.StringVar(value="42")
        self.lab1_min_steps = tk.StringVar(value="2")
        self.lab1_max_steps = tk.StringVar(value="5")
        self.lab1_min_step_time = tk.StringVar(value="2")
        self.lab1_max_step_time = tk.StringVar(value="5")
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
        self.lab1_route_step_vars = [
            [tk.StringVar() for _ in range(10)],
            [tk.StringVar() for _ in range(10)],
        ]
        self.lab1_route_input_frames = []
        self.lab1_error_strategy = tk.StringVar(value=ERROR_STRATEGIES[0])
        self.lab1_bins = tk.StringVar(value="Автоматически")

        row = 1
        fields = [
            ("Начальное значение генератора", self.lab1_seed),
            ("Минимальное количество шагов", self.lab1_min_steps),
            ("Максимальное количество шагов", self.lab1_max_steps),
            ("Минимальное время шага, с", self.lab1_min_step_time),
            ("Максимальное время шага, с", self.lab1_max_step_time),
            ("Количество имитаций для каждого Pi", self.lab1_runs),
            ("Вероятности ошибки через запятую", self.lab1_pi_text),
        ]
        for label, variable in fields:
            self._add_entry(parameters, label, variable, row)
            row += 2

        ttk.Separator(parameters).grid(row=row, column=0, sticky=EW, pady=12)
        row += 1
        ttk.Label(parameters, text="Вероятности выбора тем", style="Section.TLabel").grid(
            row=row, column=0, sticky=W, pady=(0, 4)
        )
        row += 1
        for label, variable in [
            ("Штатная работа", self.lab1_topic_normal),
            ("Восстановление", self.lab1_topic_recovery),
        ]:
            self._add_entry(parameters, f"Вероятность темы «{label}»", variable, row)
            row += 2

        ttk.Separator(parameters).grid(row=row, column=0, sticky=EW, pady=12)
        row += 1
        route_settings = ttk.Labelframe(
            parameters, text="Маршруты по подтемам", padding=8
        )
        route_settings.grid(row=row, column=0, sticky=EW)
        route_settings.columnconfigure(0, weight=1)
        self.lab1_route_input_frames = []
        for topic_index, (topic, prefix) in enumerate(
            (("Штатная работа", "A"), ("Восстановление", "B"))
        ):
            topic_frame = ttk.Labelframe(
                route_settings, text=topic, padding=6
            )
            topic_frame.grid(
                row=topic_index, column=0, sticky=EW,
                pady=(0 if topic_index == 0 else 8, 0),
            )
            topic_frame.columnconfigure(0, weight=1)
            ttk.Label(topic_frame, text="Количество маршрутов (1–10)").grid(
                row=0, column=0, sticky=W, pady=(0, 3)
            )
            count_selector = ttk.Combobox(
                topic_frame,
                textvariable=self.lab1_route_counts[topic_index],
                values=tuple(str(value) for value in range(1, 11)),
                state="readonly",
            )
            count_selector.grid(row=1, column=0, sticky=EW)
            count_selector.bind(
                "<<ComboboxSelected>>",
                lambda _event, index=topic_index: self._on_route_count_changed(index),
            )
            route_inputs = ttk.Frame(topic_frame)
            route_inputs.grid(row=2, column=0, sticky=EW, pady=(4, 0))
            self.lab1_route_input_frames.append((route_inputs, prefix))
            self._render_route_inputs(topic_index)
        ttk.Label(
            route_settings,
            text="Вероятности маршрутов одной подтемы должны в сумме давать 1. "
            "При смене количества маршрутов вероятности сбрасываются на равные. "
            "Пустая длительность шага — случайная генерация.",
            wraplength=270, bootstyle="secondary",
        ).grid(row=2, column=0, sticky=W, pady=(5, 0))
        row += 1
        ttk.Label(
            parameters,
            text="В каждом маршруте можно указать до 10 шагов — положительные целые "
            "длительности в секундах.",
            wraplength=280, bootstyle="secondary",
        ).grid(row=row, column=0, sticky=W, pady=(2, 4))
        row += 1

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
        ttk.Combobox(
            parameters, textvariable=self.lab1_bins,
            values=("Автоматически", "5", "8", "10", "15", "20"), state="readonly",
        ).grid(row=row, column=0, sticky=EW)
        row += 1

        ttk.Button(parameters, text="Запустить моделирование", bootstyle="success",
                   command=self._run_lab1).grid(row=row, column=0, sticky=EW, ipady=5, pady=(14, 0))
        row += 1
        ttk.Button(parameters, text="Сбросить параметры", bootstyle="secondary-outline",
                   command=self._reset_lab1).grid(row=row, column=0, sticky=EW, pady=(8, 0))
        row += 1
        ttk.Label(parameters, text=(
            "Стратегия ошибок применяется к моделированию ЛР1. Вероятности двух тем "
            "и маршрутов каждой подтемы должны в сумме давать 1."
        ), wraplength=280, bootstyle="secondary").grid(row=row, column=0, sticky=W, pady=(14, 0))

        ttk.Label(results, text="Результаты эксперимента", style="Section.TLabel").grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )
        metrics = ttk.Frame(results)
        metrics.grid(row=1, column=0, sticky=EW)
        for col in range(3):
            metrics.columnconfigure(col, weight=1)
        self.lab1_metric_runs = self._metric_card(metrics, "Эксперименты", "—", 0)
        self.lab1_metric_mean = self._metric_card(metrics, "Среднее время", "—", 1)
        self.lab1_metric_median = self._metric_card(metrics, "Медианное время", "—", 2)

        output = ttk.Notebook(results)
        output.grid(row=2, column=0, sticky=NSEW, pady=(14, 0))
        self.lab1_summary_frame = ttk.Frame(output, padding=8)
        self.lab1_routes_frame = ttk.Frame(output, padding=8)
        self.lab1_charts_frame = ttk.Frame(output, padding=8)
        output.add(self.lab1_summary_frame, text="Сводная таблица")
        output.add(self.lab1_routes_frame, text="Маршруты")
        output.add(self.lab1_charts_frame, text="Графики")
        self.lab1_summary_tree = self._create_tree(self.lab1_summary_frame)
        self.lab1_routes_tree = self._create_tree(self.lab1_routes_frame)
        # Прокручиваемая область для крупных графиков.
        plot_container = ttk.Frame(self.lab1_charts_frame)
        plot_container.pack(fill=BOTH, expand=YES)
        plot_container.rowconfigure(0, weight=1)
        plot_container.columnconfigure(0, weight=1)

        self.lab1_plot_view = tk.Canvas(plot_container, highlightthickness=0)
        self.lab1_plot_vscroll = ttk.Scrollbar(
            plot_container, orient=VERTICAL, command=self.lab1_plot_view.yview
        )
        self.lab1_plot_hscroll = ttk.Scrollbar(
            plot_container, orient=HORIZONTAL, command=self.lab1_plot_view.xview
        )
        self.lab1_plot_view.configure(
            yscrollcommand=self.lab1_plot_vscroll.set,
            xscrollcommand=self.lab1_plot_hscroll.set,
        )
        self.lab1_plot_view.grid(row=0, column=0, sticky=NSEW)
        self.lab1_plot_vscroll.grid(row=0, column=1, sticky=NS)
        self.lab1_plot_hscroll.grid(row=1, column=0, sticky=EW)

        self.lab1_plot_inner = ttk.Frame(self.lab1_plot_view)
        self.lab1_plot_window = self.lab1_plot_view.create_window(
            (0, 0), window=self.lab1_plot_inner, anchor="nw"
        )
        self.lab1_plot_inner.bind(
            "<Configure>",
            lambda _event: self.lab1_plot_view.configure(
                scrollregion=self.lab1_plot_view.bbox("all")
            ),
        )
        self.lab1_plot_view.bind(
            "<MouseWheel>",
            lambda event: self.lab1_plot_view.yview_scroll(
                int(-event.delta / 120), "units"
            ),
        )

        self.lab1_figure = Figure(figsize=(12, 7), dpi=100)
        self.lab1_canvas = FigureCanvasTkAgg(
            self.lab1_figure, master=self.lab1_plot_inner
        )
        self.lab1_canvas_widget = self.lab1_canvas.get_tk_widget()
        self.lab1_canvas_widget.pack(anchor="nw")
        self._draw_empty_lab1_charts()

    def _build_lab2_tab(self) -> None:
        self.lab2_tab.columnconfigure(0, weight=0, minsize=330)
        self.lab2_tab.columnconfigure(1, weight=1)
        self.lab2_tab.rowconfigure(0, weight=1)

        # Панель параметров ЛР2 прокручивается по вертикали.
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

        results = ttk.Frame(self.lab2_tab)
        results.grid(row=0, column=1, sticky=NSEW)
        results.columnconfigure(0, weight=1)
        results.rowconfigure(2, weight=1)

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

        ttk.Label(
            parameters,
            text="Вероятности ошибки оператора Pi (можно выбрать несколько)",
        ).grid(row=row, column=0, sticky=W, pady=(8, 3))
        row += 1
        pi_list_frame = ttk.Frame(parameters)
        pi_list_frame.grid(row=row, column=0, sticky=NSEW)
        row += 1
        self.lab2_pi_listbox = tk.Listbox(
            pi_list_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=7,
            width=30,
            activestyle="dotbox",
        )
        self.lab2_pi_scrollbar = ttk.Scrollbar(
            pi_list_frame, orient=VERTICAL, command=self.lab2_pi_listbox.yview
        )
        self.lab2_pi_listbox.configure(yscrollcommand=self.lab2_pi_scrollbar.set)
        self.lab2_pi_listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        self.lab2_pi_scrollbar.pack(side=RIGHT, fill=Y)
        for pi_value in self.LAB2_PI_CHOICES:
            self.lab2_pi_listbox.insert(tk.END, f"{pi_value:g}")
        default_index = self.LAB2_PI_CHOICES.index(0.1)
        self.lab2_pi_listbox.selection_set(default_index)

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

        ttk.Label(parameters, text="Стратегия обработки ошибок", style="Section.TLabel").grid(
            row=row, column=0, sticky=W, pady=(8, 4)
        )
        row += 1
        self.lab2_error_strategy = tk.StringVar(value=ERROR_STRATEGIES[0])
        ttk.Combobox(
            parameters,
            textvariable=self.lab2_error_strategy,
            values=ERROR_STRATEGIES,
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
        ttk.Label(
            parameters,
            text=(
                "Модель: один оператор, очередь FIFO и пуассоновский поток заявок. "
                "При отказе текущая и ожидающие заявки аннулируются. Заявки, "
                "поступившие во время восстановления, ожидают его окончания. "
                "Маршруты и времена шагов берутся из параметров ЛР1. Для равномерного закона "
                "используется U(0; 2m), для нормального — N(m; (0,1m)^2). "
                "Стратегия ошибок задаётся отдельно для ЛР2."
            ),
            wraplength=270, bootstyle="secondary", justify=LEFT,
        ).grid(row=row, column=0, sticky=W, pady=(14, 0))

        ttk.Label(results, text="Показатели эффективности системы", style="Section.TLabel").grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )
        metrics = ttk.Frame(results)
        metrics.grid(row=1, column=0, sticky=EW)
        for col in range(3):
            metrics.columnconfigure(col, weight=1)
        self.lab2_metric_processed = self._metric_card(metrics, "Обработано заявок (среднее)", "—", 0)
        self.lab2_metric_downtime = self._metric_card(metrics, "Время простоя (среднее)", "—", 1)
        self.lab2_metric_losses = self._metric_card(metrics, "Суммарные потери (среднее)", "—", 2)

        output = ttk.Notebook(results)
        output.grid(row=2, column=0, sticky=NSEW, pady=(14, 0))
        self.lab2_summary_frame = ttk.Frame(output, padding=8)
        self.lab2_runs_frame = ttk.Frame(output, padding=8)
        self.lab2_charts_frame = ttk.Frame(output, padding=8)
        output.add(self.lab2_summary_frame, text="Сводные показатели")
        output.add(self.lab2_runs_frame, text="Эксперименты")
        output.add(self.lab2_charts_frame, text="Графики")
        self.lab2_summary_tree = self._create_tree(self.lab2_summary_frame)
        self.lab2_runs_tree = self._create_tree(self.lab2_runs_frame)
        self.lab2_pi_frame = ttk.Frame(output, padding=8)
        output.add(self.lab2_pi_frame, text="Потери L(Pi)")
        self.lab2_pi_tree = self._create_tree(self.lab2_pi_frame)

        self.lab2_figure = Figure(figsize=(10, 5), dpi=100, constrained_layout=True)
        self.lab2_ax_losses = self.lab2_figure.add_subplot(2, 2, (1, 2))
        self.lab2_ax_decomposition = self.lab2_figure.add_subplot(2, 2, 3)
        self.lab2_ax_distribution = self.lab2_figure.add_subplot(2, 2, 4)
        self.lab2_canvas = FigureCanvasTkAgg(self.lab2_figure, master=self.lab2_charts_frame)
        self.lab2_canvas.get_tk_widget().pack(fill=BOTH, expand=YES)
        self.lab2_result = None
        self._draw_empty_lab2_charts()

    @staticmethod
    def _add_entry(parent, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=(4, 3))
        ttk.Entry(parent, textvariable=variable).grid(row=row + 1, column=0, sticky=EW)

    def _render_route_inputs(self, topic_index: int) -> None:
        route_frame, prefix = self.lab1_route_input_frames[topic_index]
        for child in route_frame.winfo_children():
            child.destroy()

        route_count = int(self.lab1_route_counts[topic_index].get())
        route_frame.columnconfigure(0, weight=1)
        for index in range(route_count):
            route_name = f"{prefix}{index + 1}"
            row = index * 5
            ttk.Label(
                route_frame, text=f"Маршрут {route_name}", style="Section.TLabel"
            ).grid(row=row, column=0, sticky=W, pady=(4, 0))
            self._add_entry(
                route_frame,
                f"Вероятность выбора {route_name}",
                self.lab1_route_probability_vars[topic_index][index],
                row + 1,
            )
            self._add_entry(
                route_frame,
                f"Шаги {route_name}, длительности через запятую (с)",
                self.lab1_route_step_vars[topic_index][index],
                row + 3,
            )

    def _on_route_count_changed(self, topic_index: int) -> None:
        route_count = int(self.lab1_route_counts[topic_index].get())
        # probability = f"{1 / route_count:.6g}"
        probability = repr(1 / route_count)
        for variable in self.lab1_route_probability_vars[topic_index][:route_count]:
            variable.set(probability)
        self._render_route_inputs(topic_index)

    def _get_lab1_route_data(
        self,
    ) -> tuple[
        tuple[int, int],
        tuple[float, ...],
        tuple[tuple[int, ...] | None, ...],
    ]:
        route_counts = tuple(int(variable.get()) for variable in self.lab1_route_counts)
        route_probabilities = []
        route_steps = []
        for topic_index, (count, prefix) in enumerate(zip(route_counts, ("A", "B"))):
            for index in range(count):
                name = f"{prefix}{index + 1}"
                try:
                    probability = float(
                        self.lab1_route_probability_vars[topic_index][index].get()
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"Укажите вероятность выбора маршрута {name}."
                    ) from exc
                route_probabilities.append(probability)
                route_steps.append(
                    self._parse_route_steps(
                        self.lab1_route_step_vars[topic_index][index].get()
                    )
                )
        return route_counts, tuple(route_probabilities), tuple(route_steps)

    @staticmethod
    def _parse_route_steps(value: str) -> tuple[int, ...] | None:
        value = value.strip()
        if not value:
            return None

        parts = [part.strip() for part in value.split(",")]
        if len(parts) > 10:
            raise ValueError("В маршруте нельзя указать больше 10 шагов.")
        if any(not part for part in parts):
            raise ValueError("Длительности шагов нужно разделять запятыми без пустых значений.")

        try:
            steps = tuple(int(part) for part in parts)
        except ValueError as exc:
            raise ValueError("Длительности шагов должны быть целыми числами.") from exc

        if any(step <= 0 for step in steps):
            raise ValueError("Длительность каждого шага должна быть больше 0.")
        return steps

    @staticmethod
    def _metric_card(parent, title: str, value: str, column: int):
        card = ttk.Frame(parent, padding=12, bootstyle="light")
        card.grid(row=0, column=column, sticky=EW, padx=(0 if column == 0 else 8, 0))
        ttk.Label(card, text=title, bootstyle="secondary").pack(anchor=W)
        value_label = ttk.Label(card, text=value, style="Metric.TLabel")
        value_label.pack(anchor=W, pady=(5, 0))
        return value_label

    @staticmethod
    def _create_tree(parent):
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill=BOTH, expand=YES)
        tree = tkttk.Treeview(wrapper, show="headings")
        y_scroll = ttk.Scrollbar(wrapper, orient=VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(wrapper, orient=HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky=NSEW)
        y_scroll.grid(row=0, column=1, sticky=NS)
        x_scroll.grid(row=1, column=0, sticky=EW)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        return tree

    @staticmethod
    def _fill_tree(tree, dataframe) -> None:
        tree.delete(*tree.get_children())
        columns = list(dataframe.columns)
        tree["columns"] = columns
        for column in columns:
            tree.heading(column, text=str(column))
            tree.column(column, width=145, minwidth=90, anchor=CENTER, stretch=True)
        for row in dataframe.itertuples(index=False, name=None):
            values = []
            for value in row:
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                values.append(value)
            tree.insert("", END, values=values)

    def _draw_empty_lab1_charts(self) -> None:
        self.lab1_figure.clear()
        ax_hist = self.lab1_figure.add_subplot(1, 2, 1)
        ax_mean = self.lab1_figure.add_subplot(1, 2, 2)
        ax_hist.set_title("Распределение времени")
        ax_hist.set_xlabel("Время, с")
        ax_hist.set_ylabel("Частота")
        ax_mean.set_title("Среднее время от Pi")
        ax_mean.set_xlabel("Вероятность ошибки Pi")
        ax_mean.set_ylabel("Среднее время, с")
        self.lab1_figure.subplots_adjust(left=0.07, right=0.98, top=0.95, bottom=0.08)
        self._sync_canvas_widget_size()
        self.lab1_canvas.draw_idle()
        self.lab1_canvas.draw()
        self.lab1_canvas_widget.update_idletasks()
        self.lab1_plot_view.configure(
            scrollregion=(0, 0,
                        self.lab1_canvas_widget.winfo_reqwidth(),
                        self.lab1_canvas_widget.winfo_reqheight())
        )


    def _sync_canvas_widget_size(self) -> None:
        """Явно выставляет размер Tk-виджета канваса из figsize*dpi."""
        w = int(self.lab1_figure.get_figwidth() * self.lab1_figure.dpi)
        h = int(self.lab1_figure.get_figheight() * self.lab1_figure.dpi)
        self.lab1_canvas_widget.configure(width=w, height=h)

    def _run_lab1(self) -> None:
        try:
            n_simulations = int(self.lab1_runs.get())
            seed = int(self.lab1_seed.get())
            min_steps = int(self.lab1_min_steps.get())
            max_steps = int(self.lab1_max_steps.get())
            min_step_time = int(self.lab1_min_step_time.get())
            max_step_time = int(self.lab1_max_step_time.get())
            selected_pi = tuple(float(x.strip()) for x in self.lab1_pi_text.get().split(",") if x.strip())
            if not selected_pi:
                raise ValueError("Введите хотя бы одну вероятность ошибки Pi через запятую.")
            topic_probabilities = (float(self.lab1_topic_normal.get()), float(self.lab1_topic_recovery.get()))
            route_counts, route_probabilities, route_steps = self._get_lab1_route_data()

            bins_value = self.lab1_bins.get()
            bins = None if bins_value == "Автоматически" else int(bins_value)

            config = Lab1Config(
                n_simulations=n_simulations,
                seed=seed,
                min_steps=min_steps,
                max_steps=max_steps,
                min_step_time=min_step_time,
                max_step_time=max_step_time,
                error_probabilities=selected_pi,
                topic_probabilities=topic_probabilities,
                route_counts=route_counts,
                route_probabilities=route_probabilities,
                route_steps=route_steps,
                error_strategy=self.lab1_error_strategy.get(),
            )

            self.status_var.set("Выполняется моделирование лабораторной №1…")
            self.root.update_idletasks()

            result = run_lab1(config)
            self.lab1_result = result

            # Пересчитываем число интервалов по выбранной настройке.
            histogram_bins = get_histogram_bins(n_simulations, bins)

            self._fill_tree(self.lab1_summary_tree, result["summary_df"])
            self._fill_tree(self.lab1_routes_tree, result["routes_df"])

            results_df = result["results_df"]
            mean_time = results_df["time"].mean()
            median_time = results_df["time"].median()
            self.lab1_metric_runs.configure(text=f"{len(results_df):,}".replace(",", " "))
            self.lab1_metric_mean.configure(text=f"{mean_time:.2f} с")
            self.lab1_metric_median.configure(text=f"{median_time:.2f} с")

            self._draw_lab1_charts(result, histogram_bins)
            self.status_var.set(
                f"ЛР №1 завершена: {n_simulations} имитаций для каждого Pi; "
                f"всего {len(results_df)} наблюдений."
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


    def _draw_lab1_charts(self, result, bins: int) -> None:
        results_df = result["results_df"]
        summary_df = result["summary_df"]

        pi_values = sorted(results_df["Pi"].unique())
        n_hist_rows = (len(pi_values) + 1) // 2
        total_rows = n_hist_rows + 1

        figure_height = max(7, n_hist_rows * 4.5 + 4.0)
        self.lab1_figure.clear()
        self.lab1_figure.set_size_inches(12, figure_height, forward=True)
        self._sync_canvas_widget_size()
        grid = self.lab1_figure.add_gridspec(
            total_rows, 2, hspace=0.48, wspace=0.28
        )

        for index, pi in enumerate(pi_values):
            row = index // 2
            col = index % 2
            ax = self.lab1_figure.add_subplot(grid[row, col])
            sample = results_df.loc[results_df["Pi"] == pi, "time"]
            ax.hist(sample, bins=bins, edgecolor="black", alpha=0.75)
            ax.set_title(f"Время диалога при Pi = {pi:g}", fontsize=13, pad=10)
            ax.set_xlabel("Время выполнения, с")
            ax.set_ylabel("Частота")
            ax.grid(axis="y", alpha=0.25)

        ax_mean = self.lab1_figure.add_subplot(grid[n_hist_rows, :])
        ax_mean.plot(
            summary_df["Pi"],
            summary_df["Среднее_время"],
            marker="o",
            linewidth=2.5,
            markersize=7,
        )
        ax_mean.set_title(
            "Влияние вероятности ошибки на среднее время", fontsize=14, pad=12
        )
        ax_mean.set_xlabel("Вероятность ошибки Pi")
        ax_mean.set_ylabel("Среднее время, с")
        ax_mean.grid(True, alpha=0.25)

        self.lab1_figure.subplots_adjust(
            left=0.07, right=0.98, top=0.95, bottom=0.06,
            hspace=0.55, wspace=0.28,
        )

        self.lab1_canvas.draw()
        self.lab1_plot_inner.update_idletasks()
        w = self.lab1_canvas_widget.winfo_reqwidth()
        h = self.lab1_canvas_widget.winfo_reqheight()
        self.lab1_plot_view.configure(scrollregion=(0, 0, w, h))
        self.lab1_plot_view.xview_moveto(0)
        self.lab1_plot_view.yview_moveto(0)

    def _draw_empty_lab2_charts(self) -> None:
        self.lab2_ax_losses.clear()
        self.lab2_ax_decomposition.clear()
        self.lab2_ax_distribution.clear()
        self.lab2_ax_losses.set_title("L(Pi) — суммарные потери")
        self.lab2_ax_decomposition.set_title("Разложение L(Pi): R1- и R2-компоненты")
        self.lab2_ax_distribution.set_title("Распределение суммарных потерь")
        self.lab2_canvas.draw_idle()

    def _get_lab2_pi_values(self) -> tuple[float, ...]:
        selected = tuple(
            float(self.lab2_pi_listbox.get(index))
            for index in self.lab2_pi_listbox.curselection()
        )
        if not selected:
            raise ValueError(
                "Выберите хотя бы одно значение вероятности ошибки Pi "
                "(удерживайте Ctrl или Shift для множественного выбора)."
            )
        return selected

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
                error_strategy=self.lab2_error_strategy.get(),
            )

            route_counts, route_probabilities, route_steps = self._get_lab1_route_data()

            # Для ЛР2 используются те же маршруты диалога, что и в ЛР1.
            route_config = Lab1Config(
                n_simulations=1,
                seed=config.seed,
                min_steps=int(self.lab1_min_steps.get()),
                max_steps=int(self.lab1_max_steps.get()),
                min_step_time=int(self.lab1_min_step_time.get()),
                max_step_time=int(self.lab1_max_step_time.get()),
                error_probabilities=(0.0,),
                topic_probabilities=(
                    float(self.lab1_topic_normal.get()),
                    float(self.lab1_topic_recovery.get()),
                ),
                route_counts=route_counts,
                route_probabilities=route_probabilities,
                route_steps=route_steps,
            )
            routes = generate_routes(route_config)

            self.status_var.set("Выполняется моделирование лабораторной №2…")
            self.root.update_idletasks()
            result = run_lab2(config, routes)
            self.lab2_result = result

            pi_summary = result["pi_summary_df"]
            overall_losses = float(
                result["runs_df"]["Суммарные потери"].mean()
            )
            self.lab2_metric_processed.configure(
                text=f"{float(result['runs_df']['Обработано заявок'].mean()):.1f}"
            )
            self.lab2_metric_downtime.configure(
                text=f"{float(result['runs_df']['Время простоя, с'].mean()):.2f} с"
            )
            self.lab2_metric_losses.configure(text=f"{overall_losses:.2f}")
            self._fill_tree(self.lab2_summary_tree, result["summary_df"])
            self._fill_tree(self.lab2_runs_tree, result["runs_df"])
            self._fill_tree(self.lab2_pi_tree, pi_summary)
            self._draw_lab2_charts(result)
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

    def _draw_lab2_charts(self, result) -> None:
        runs = result["runs_df"]
        pi_summary = result["pi_summary_df"].sort_values("Pi")

        self.lab2_ax_losses.clear()
        self.lab2_ax_decomposition.clear()
        self.lab2_ax_distribution.clear()

        pi_values = pi_summary["Pi"].to_numpy(dtype=float)

        # 1. Главная кривая — суммарные потери L(Pi).
        mean_losses = pi_summary["Суммарные потери"].to_numpy(dtype=float)
        std_losses = pi_summary["Суммарные потери — Стд. отклонение"].to_numpy(dtype=float)
        ax = self.lab2_ax_losses
        ax.errorbar(
            pi_values, mean_losses, yerr=std_losses,
            marker="o", linewidth=2.5, markersize=7, capsize=4,
            label="L(Pi) — средние суммарные потери",
        )
        for pi, loss in zip(pi_values, mean_losses):
            ax.annotate(f"{loss:,.0f}", (pi, loss), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=8)
        ax.set_title("Зависимость суммарных потерь L от вероятности ошибки Pi",
                     fontsize=13, pad=10)
        ax.set_xlabel("Вероятность ошибки оператора Pi")
        ax.set_ylabel("Суммарные потери L(Pi)")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")

        # 2. Разложение L(Pi) на R1- и R2-компоненты.
        r1_component = pi_summary["Потери от задержек"].to_numpy(dtype=float)
        r2_component = pi_summary["Потери от простоя"].to_numpy(dtype=float)
        dominant_r1 = r1_component.mean() >= r2_component.mean()
        dominant_label = "R1 (задержки)" if dominant_r1 else "R2 (простой)"

        ax_dec = self.lab2_ax_decomposition
        ax_dec.plot(
            pi_values, r1_component,
            marker="s", linewidth=2.2, color="tab:blue",
            label="R1-компонента (задержки заявок)",
        )
        ax_dec.plot(
            pi_values, r2_component,
            marker="^", linewidth=2.2, color="tab:orange",
            label="R2-компонента (простой системы)",
        )
        ax_dec.fill_between(pi_values, r1_component, r2_component, alpha=0.12, color="grey")
        ax_dec.set_title(f"Разложение L(Pi): доминирует {dominant_label}",
                        fontsize=12, pad=10)
        ax_dec.set_xlabel("Вероятность ошибки оператора Pi")
        ax_dec.set_ylabel("Компоненты потерь")
        ax_dec.grid(True, alpha=0.25)
        ax_dec.legend(loc="best", fontsize=9)

        # 3. Гистограмма суммарных потерь (по всем прогонам).
        self.lab2_ax_distribution.hist(runs["Суммарные потери"], bins="auto",
                                       edgecolor="black", alpha=0.8)
        self.lab2_ax_distribution.set_title("Распределение суммарных потерь")
        self.lab2_ax_distribution.set_xlabel("Суммарные потери")
        self.lab2_ax_distribution.set_ylabel("Частота")
        self.lab2_ax_distribution.grid(axis="y", alpha=0.25)

        self.lab2_figure.tight_layout()
        self.lab2_canvas.draw_idle()

    def _reset_lab1(self) -> None:
        defaults = {
            self.lab1_seed: "42",
            self.lab1_min_steps: "2",
            self.lab1_max_steps: "5",
            self.lab1_min_step_time: "2",
            self.lab1_max_step_time: "5",
            self.lab1_runs: "10000",
            self.lab1_pi_text: "0, 0.3, 0.6, 0.9",
            self.lab1_topic_normal: "0.8",
            self.lab1_topic_recovery: "0.2",
            self.lab1_error_strategy: ERROR_STRATEGIES[0],
            self.lab1_bins: "Автоматически",
        }
        for variable, value in defaults.items():
            variable.set(value)
        for variable in self.lab1_route_counts:
            variable.set("2")
        for topic_index, values in enumerate(
            (("0.6", "0.4"), ("0.7", "0.3"))
        ):
            for index, variable in enumerate(
                self.lab1_route_probability_vars[topic_index]
            ):
                variable.set(values[index] if index < len(values) else "0")
            for variable in self.lab1_route_step_vars[topic_index]:
                variable.set("")
            self._render_route_inputs(topic_index)
        self.lab1_metric_runs.configure(text="—")
        self.lab1_metric_mean.configure(text="—")
        self.lab1_metric_median.configure(text="—")
        self.lab1_summary_tree.delete(*self.lab1_summary_tree.get_children())
        self.lab1_routes_tree.delete(*self.lab1_routes_tree.get_children())
        self.lab1_result = None
        self._draw_empty_lab1_charts()
        self.status_var.set("Параметры лабораторной №1 сброшены")

    def _reset_lab2(self) -> None:
        self.lab2_arrival_rate.set("0.05")
        self.lab2_failure_mean.set("100")
        self.lab2_r1.set("1.0")
        self.lab2_r2.set("5.0")
        self.lab2_duration.set("1000")
        self.lab2_runs.set("100")
        for index in range(self.lab2_pi_listbox.size()):
            self.lab2_pi_listbox.selection_clear(index)
        self.lab2_pi_listbox.selection_set(self.LAB2_PI_CHOICES.index(0.1))
        self.lab2_seed.set("42")
        self.lab2_distribution.set("Экспоненциальный")
        self.lab2_error_strategy.set(ERROR_STRATEGIES[0])
        self.lab2_metric_processed.configure(text="—")
        self.lab2_metric_downtime.configure(text="—")
        self.lab2_metric_losses.configure(text="—")
        self.lab2_summary_tree.delete(*self.lab2_summary_tree.get_children())
        self.lab2_runs_tree.delete(*self.lab2_runs_tree.get_children())
        self.lab2_result = None
        self._draw_empty_lab2_charts()
        self.status_var.set("Параметры лабораторной №2 сброшены")

    def on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    HumanMachineApp().run()
