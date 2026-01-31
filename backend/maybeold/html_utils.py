import json
from pathlib import Path
from typing import Optional
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import matplotlib.pyplot

from html_report import PDFReporter


def create_report_pdf(
    key: str, result: dict, template_path: Path | str, scale: Optional[float] = None
):
    # print(result[key].keys())
    if isinstance(template_path, str):
        template_path = Path(template_path)
    font_geneva = {"fontname": "Calibri"}
    textbox_kwargs = {
        "backgroundcolor": "#242526",
        "alpha": 0.8,
        "color": "white",
        "fontweight": 900,
        "multialignment": "center",
        "horizontalalignment": "center",
        "fontsize": 16,
    }
    textbox_kwargs.update(font_geneva)
    font_geneva_title = {"fontname": "Calibri", "weight": "bold", "fontsize": 20}
    sum = 0
    decs = 0
    tat_graph = Path(f"temp/{key}-tat.svg")
    approval_graph = Path(f"temp/{key}-approval.svg")
    print("ˇˇˇˇ" + key + "ˇˇˇˇ")
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    plt.pie(
        (
            result[key]["Same_Day_Rate"] * 100,
            100 - float((result[key]["Same_Day_Rate"])) * 100,
        ),
        shadow=False,
        radius=1.1,
        colors=["#13477d", "#f0ad00"],
    )
    plt.title("Percent of Messages Completed Within 24 Hours", **font_geneva_title)
    legend = plt.legend(
        ["Completed Same Day", "Completed >24 Hours"],
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
    plt.figtext(
        0.5,
        0.2,
        f"Completed Within 24 Hours:\n{'{:.0f}%'.format(float(result[key]['Same_Day_Rate'] * 100))}",
        **textbox_kwargs,
    )
    p = plt.gcf()
    my_circle = plt.Circle((0, 0), 0.55, color="white")
    p.gca().add_artist(my_circle)
    plt.savefig(tat_graph, format="svg")
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    inscope_requests = result[key]["InScope_Requests"]
    handled_msgs = result[key]["Handled_Messages"]
    approval_rate = handled_msgs / inscope_requests if inscope_requests > 0 else 0
    approval_percent = f"{approval_rate * 100}%"
    # pie = plt.pie(
    #     [
    #         result[key]["Tableau Approval Rate"],
    #         100 - float(result[key]["Tableau Approval Rate"][:-1]),
    #     ],
    #     radius=1.1,
    #     startangle=90,
    #     colors=["#13477d", "#f0ad00"],
    # )
    pie = plt.pie(
        [approval_rate * 100, 100 - approval_rate * 100],
        radius=1.1,
        startangle=90,
        colors=["#13477d", "#f0ad00"],
    )
    plt.title("Refill Center Approval Rate", **font_geneva_title)
    legend = plt.legend(
        ["Refill Center Handled", "Routed to Provider for Review"],
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
    plt.figtext(
        0.5,
        0.2,
        f"Refill Center Handled:\n{'{:.0f}%'.format(approval_rate * 100)}",
        **textbox_kwargs,
    )
    q = plt.gcf()
    my_circle2 = plt.Circle((0, 0), 0.55, color="white")
    q.gca().add_artist(my_circle2)
    plt.savefig(approval_graph, format="svg")
    reporter = PDFReporter(
        name=key,
        json_file="./content/content.json",
        html_template=template_path.absolute().as_posix(),
        approval_graph=approval_graph,
        tat_graph=tat_graph,
    )
    metrics = [
        int(result[key]["Decisions"]),
        f"{result[key]['Approval_Rate'] * 100:.1f}%",
        f"{result[key]['Same_Day_Rate'] * 100:.1f}%",
    ]
    metrics_labels = [
        "Medication refills addressed - ",
        "Percentage of refills handled by Refill Center - ",
        "Percentage of encounters with 24H Turnaround Time - ",
    ]

    metrics_text = [str(x) + str(y) for x, y in zip(metrics_labels, metrics)]
    reporter_dict = {"Metrics": metrics_text}
    # TODO: Just pass reporter_dict to the create_report fn)
    reporter.json_obj = reporter_dict
    reporter.create_report(
        template_path=template_path.as_posix(), new_text=True, scale=scale
    )
    plt.close("all")
    print("^^^^" + key + "^^^^")
