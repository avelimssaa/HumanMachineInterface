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

from models.lab1_model import Lab1Config, run_lab1, get_histogram_bins


APP_TITLE = "Человеко-машинный интерфейс"
APP_VERSION = "0.3.0"


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
        self.lab1_route_a1 = tk.StringVar(value="0.6")
        self.lab1_route_a2 = tk.StringVar(value="0.4")
        self.lab1_route_b1 = tk.StringVar(value="0.7")
        self.lab1_route_b2 = tk.StringVar(value="0.3")
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
        ttk.Label(parameters, text="Вероятности выбора подтем", style="Section.TLabel").grid(
            row=row, column=0, sticky=W, pady=(0, 4)
        )
        row += 1
        for label, variable in [
            ("Маршрут A1", self.lab1_route_a1),
            ("Маршрут A2", self.lab1_route_a2),
            ("Маршрут B1", self.lab1_route_b1),
            ("Маршрут B2", self.lab1_route_b2),
        ]:
            self._add_entry(parameters, f"Вероятность {label}", variable, row)
            row += 2

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
            "При ошибке текущий шаг выполняется повторно. Вероятности двух тем "
            "и каждой пары маршрутов должны в сумме давать 1."
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
        # self.lab1_canvas_widget.pack(anchor="nw")
        # self.lab1_canvas_widget.grid(row=0, column=0, sticky="nsew")
        self.lab1_canvas_widget.grid(row=0, column=0, sticky="nw")
        # self.lab1_plot_inner.rowconfigure(0, weight=1)
        # self.lab1_plot_inner.columnconfigure(0, weight=1)
        self._draw_empty_lab1_charts()

    def _build_lab2_tab(self) -> None:
        self.lab2_tab.columnconfigure(0, weight=0, minsize=310)
        self.lab2_tab.columnconfigure(1, weight=1)
        self.lab2_tab.rowconfigure(0, weight=1)

        parameters = ttk.Labelframe(
            self.lab2_tab, text="Параметры системы", padding=14
        )
        parameters.grid(row=0, column=0, sticky=NSEW, padx=(0, 12))
        parameters.columnconfigure(0, weight=1)

        results = ttk.Frame(self.lab2_tab)
        results.grid(row=0, column=1, sticky=NSEW)
        results.columnconfigure(0, weight=1)
        results.rowconfigure(1, weight=1)

        ttk.Label(
            parameters, text="Исходные параметры", style="Section.TLabel"
        ).grid(row=0, column=0, sticky=W, pady=(0, 12))

        self.lab2_arrival_rate = tk.StringVar(value="1.0")
        self.lab2_failure_mean = tk.StringVar(value="100.0")
        self.lab2_r1 = tk.StringVar(value="1.0")
        self.lab2_r2 = tk.StringVar(value="5.0")
        self.lab2_duration = tk.StringVar(value="1000")
        self.lab2_runs = tk.StringVar(value="100")

        self._add_entry(parameters, "Интенсивность поступления заявок", self.lab2_arrival_rate, 1)
        self._add_entry(parameters, "Средняя наработка на отказ", self.lab2_failure_mean, 3)
        self._add_entry(parameters, "Удельные потери R1 (задержка)", self.lab2_r1, 5)
        self._add_entry(parameters, "Удельные потери R2 (простой)", self.lab2_r2, 7)
        self._add_entry(parameters, "Время моделирования", self.lab2_duration, 9)
        self._add_entry(parameters, "Количество экспериментов", self.lab2_runs, 11)

        ttk.Label(parameters, text="Закон наработки на отказ").grid(
            row=13, column=0, sticky=W, pady=(12, 4)
        )
        self.lab2_distribution = tk.StringVar(value="Экспоненциальный")
        ttk.Combobox(
            parameters,
            textvariable=self.lab2_distribution,
            values=("Экспоненциальный", "Равномерный", "Нормальный"),
            state="readonly",
        ).grid(row=14, column=0, sticky=EW)

        ttk.Separator(parameters).grid(row=15, column=0, sticky=EW, pady=16)
        ttk.Button(
            parameters,
            text="Запустить моделирование",
            bootstyle="success",
            command=self._lab2_not_implemented,
        ).grid(row=16, column=0, sticky=EW, ipady=5)
        ttk.Button(
            parameters,
            text="Сбросить параметры",
            bootstyle="secondary-outline",
            command=self._reset_lab2,
        ).grid(row=17, column=0, sticky=EW, pady=(8, 0))

        ttk.Label(
            parameters,
            text=(
                "Параметры являются начальными значениями интерфейса. "
                "Перед расчётами уточним их смысл и единицы по варианту задания."
            ),
            wraplength=265,
            bootstyle="secondary",
        ).grid(row=18, column=0, sticky=W, pady=(18, 0))

        ttk.Label(
            results, text="Показатели эффективности системы", style="Section.TLabel"
        ).grid(row=0, column=0, sticky=W, pady=(0, 10))

        metrics = ttk.Frame(results)
        metrics.grid(row=1, column=0, sticky=EW)
        for col in range(3):
            metrics.columnconfigure(col, weight=1)
        self._metric_card(metrics, "Обработано заявок", "—", 0)
        self._metric_card(metrics, "Время простоя", "—", 1)
        self._metric_card(metrics, "Суммарные потери", "—", 2)

        output = ttk.Labelframe(results, text="Анализ результатов", padding=12)
        output.grid(row=2, column=0, sticky=NSEW, pady=(14, 0))
        results.rowconfigure(2, weight=1)
        ttk.Label(
            output,
            text=(
                "Модель эффективности человеко-машинной системы будет "
                "реализована отдельно по методическим указаниям."
            ),
            justify=CENTER,
            bootstyle="secondary",
        ).pack(expand=YES)

    @staticmethod
    def _add_entry(parent, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=W, pady=(4, 3))
        ttk.Entry(parent, textvariable=variable).grid(row=row + 1, column=0, sticky=EW)

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
            route_probabilities = (
                float(self.lab1_route_a1.get()), float(self.lab1_route_a2.get()),
                float(self.lab1_route_b1.get()), float(self.lab1_route_b2.get()),
            )

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
                route_probabilities=route_probabilities,
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

        # self.lab1_figure.tight_layout()
        self.lab1_figure.subplots_adjust(
            left=0.07, right=0.98, top=0.95, bottom=0.06,
            hspace=0.55, wspace=0.28,
        )
        # self.lab1_canvas.draw_idle()
        self.lab1_canvas.draw()
        self.lab1_plot_inner.update_idletasks()
        # self.lab1_plot_view.configure(
        #     scrollregion=self.lab1_plot_view.bbox("all")
        # )
        w = self.lab1_canvas_widget.winfo_reqwidth()
        h = self.lab1_canvas_widget.winfo_reqheight()
        self.lab1_plot_view.configure(scrollregion=(0, 0, w, h))
        self.lab1_plot_view.xview_moveto(0)
        self.lab1_plot_view.yview_moveto(0)

    def _sync_canvas_widget_size(self) -> None:
        """Явно выставляет размер Tk-виджета канваса из figsize*dpi."""
        w = int(self.lab1_figure.get_figwidth() * self.lab1_figure.dpi)
        h = int(self.lab1_figure.get_figheight() * self.lab1_figure.dpi)
        self.lab1_canvas_widget.configure(width=w, height=h)

    def _lab2_not_implemented(self) -> None:
        messagebox.showinfo(
            "Лабораторная №2",
            "Интерфейс ЛР2 подготовлен. Вычислительная модель будет "
            "реализована отдельно по методическим указаниям.",
            parent=self.root,
        )

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
            self.lab1_route_a1: "0.6",
            self.lab1_route_a2: "0.4",
            self.lab1_route_b1: "0.7",
            self.lab1_route_b2: "0.3",
            self.lab1_bins: "Автоматически",
        }
        for variable, value in defaults.items():
            variable.set(value)
        self.lab1_metric_runs.configure(text="—")
        self.lab1_metric_mean.configure(text="—")
        self.lab1_metric_median.configure(text="—")
        self.lab1_summary_tree.delete(*self.lab1_summary_tree.get_children())
        self.lab1_routes_tree.delete(*self.lab1_routes_tree.get_children())
        self.lab1_result = None
        self._draw_empty_lab1_charts()
        self.status_var.set("Параметры лабораторной №1 сброшены")

    def _reset_lab2(self) -> None:
        self.lab2_arrival_rate.set("1.0")
        self.lab2_failure_mean.set("100.0")
        self.lab2_r1.set("1.0")
        self.lab2_r2.set("5.0")
        self.lab2_duration.set("1000")
        self.lab2_runs.set("100")
        self.lab2_distribution.set("Экспоненциальный")
        self.status_var.set("Параметры лабораторной №2 сброшены")

    def on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    HumanMachineApp().run()
