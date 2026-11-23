"""Общие UI-хелперы: таблицы и т.п."""

import tkinter as tk
from tkinter import ttk as tkttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def create_tree(parent):
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


def fill_tree(tree, dataframe):
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


def fill_tree_with_pi_separators(tree, dataframe, pi_column="Pi") -> None:
    tree.delete(*tree.get_children())
    columns = list(dataframe.columns)
    tree["columns"] = columns
    for column in columns:
        tree.heading(column, text=str(column))
        tree.column(column, width=145, minwidth=90, anchor=CENTER, stretch=True)

    pi_values = sorted(dataframe[pi_column].unique())
    for index, pi in enumerate(pi_values):
        subset = dataframe[dataframe[pi_column] == pi]
        for row in subset.itertuples(index=False, name=None):
            values = []
            for value in row:
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                values.append(value)
            tree.insert("", END, values=values)

        if index < len(pi_values) - 1:
            tree.insert("", END, values=[""] * len(columns), tags=("separator",))

    tree.tag_configure("separator", background="#e0e0e0")