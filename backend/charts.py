from pathlib import Path
from typing import Any, Collection, List, Optional

from matplotlib import pyplot as plt, ticker
import matplotlib.patheffects as path_effects

font_geneva_title = {"fontname": "Calibri", "weight": "bold", "fontsize": 20}
font_geneva = {"fontname": "Calibri"}

# colors
navy = "#13477d"
yellow = "#f0ad00"

# def get_textbox_kwargs(key:str,value):
#     textbox_kwargs = {
#         "backgroundcolor": "#242526",
#         "alpha": 0.8,
#         "color": "white",
#         "fontweight": 900,
#         "multialignment": "center",
#         "horizontalalignment": "center",
#         "fontsize": 16,
#     }
#     textbox_kwargs.update({key:value})
#     return


def get_textbox_kwargs(kwarg: Optional[dict[str, Any]] = None):
    textbox_kwargs = {
        "backgroundcolor": "#242526",
        "alpha": 0.8,
        "color": "white",
        "fontweight": 900,
        "multialignment": "center",
        "horizontalalignment": "center",
        "fontsize": 16,
    }
    if kwarg:
        textbox_kwargs.update(kwarg)
    return textbox_kwargs


def create_donut_chart(
    value: float | int,
    title: str,
    export_path: Path,
    label_1: str = "Label 1",
    label_2: str = "Label 1",
):
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    whole = 1 if value < 1 else 100
    plt.pie(
        (
            value,
            whole - value,
        ),
        shadow=False,
        radius=1.1,
        colors=[navy, yellow],
    )
    plt.title(title, **font_geneva_title)
    legend = plt.legend(
        [label_1, label_2],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fancybox=True,
        shadow=False,
        ncol=2,
        frameon=True,
        edgecolor="#f2f2f2",
        facecolor="#fbfbfb",
        framealpha=0.3,
        prop={"size": 12},
    )
    bbox = legend.get_frame().set_path_effects(
        [
            path_effects.SimpleLineShadow(alpha=0.8, shadow_color="#fafafa"),
            path_effects.Normal(),
            path_effects.withSimplePatchShadow(alpha=0.1, shadow_rgbFace="gray"),
        ]
    )
    plt.figtext(0.5, 0.2, f"{label_1}\n{value}%", get_textbox_kwargs())
    p = plt.gcf()
    my_circle = plt.Circle((0, 0), 0.55, color="white")
    p.gca().add_artist(my_circle)
    plt.savefig(export_path, format="svg")
    with open(export_path, "r") as svg_file:
        svg_txt = svg_file.read()
        return svg_txt


def create_bar_chart(
    values: Collection[float | int],
    labels: Collection[str],
    title: str,
    export_path: Path,
    legend_label: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
):
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300, layout="constrained")
    plt.bar(labels, values, 1, color=navy)
    plt.title(title, **font_geneva_title)
    legend = plt.legend(
        [legend_label],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fancybox=True,
        shadow=False,
        ncol=2,
        frameon=True,
        edgecolor="#f2f2f2",
        facecolor="#fbfbfb",
        framealpha=0.3,
        prop={"size": 12},
    )
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax.set_ylim(0, max(values) + 1)
    if x_label:
        ax.set_xlabel(x_label, fontsize=12)
    if y_label:
        ax.set_ylabel(y_label, fontsize=12)
    legend.get_frame().set_path_effects(
        [
            path_effects.SimpleLineShadow(alpha=0.8, shadow_color="#fafafa"),
            path_effects.Normal(),
            path_effects.withSimplePatchShadow(alpha=0.1, shadow_rgbFace="gray"),
        ]
    )
    plt.savefig(export_path, format="svg")
    with open(export_path, "r") as svg_file:
        svg_txt = svg_file.read()
        return svg_txt


def create_dual_bar_chart(
    values: List[float | int],
    labels: List[str],
    title: str,
    export_path: Path,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
):
    if len(set(labels)) != len(labels):
        raise ValueError("Duplicate labels")
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    colors = [navy, yellow]
    bars = [ax.bar(labels[i], values[i], color=colors[i]) for i in range(len(values))]
    plt.bar(labels, values, 1, color=[navy, yellow])
    plt.title(title, **font_geneva_title)
    legend = plt.legend(
        # labels,
        handles=bars,
        labels=labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fancybox=True,
        shadow=False,
        ncol=2,
        frameon=True,
        edgecolor="#f2f2f2",
        facecolor="#fbfbfb",
        framealpha=0.3,
        prop={"size": 12},
    )
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax.set_ylim(0, max(values) + 1)
    if x_label:
        ax.set_xlabel(x_label, fontsize=12)
    if y_label:
        ax.set_ylabel(y_label, fontsize=12)
    legend.get_frame().set_path_effects(
        [
            path_effects.SimpleLineShadow(alpha=0.8, shadow_color="#fafafa"),
            path_effects.Normal(),
            path_effects.withSimplePatchShadow(alpha=0.1, shadow_rgbFace="gray"),
        ]
    )
    plt.savefig(export_path, format="svg")
    with open(export_path, "r") as svg_file:
        svg_txt = svg_file.read()
        return svg_txt


if __name__ == "__main__":
    print(create_donut_chart(55, "%", Path("donut.svg").absolute(), "full", "empty"))
    print(
        create_bar_chart(
            [1, 2, 3, 4],
            ["a", "b", "c", "d"],
            "SomethingBar",
            Path("bar.svg"),
            "Months",
            "Refills",
        )
    )
