import asyncio
import base64
from functools import cache
from io import BytesIO
from pathlib import Path
from typing import NamedTuple, Optional, Tuple, TypedDict
import bs4
from matplotlib import pyplot as plt
import matplotlib.patheffects as path_effects
import pandas as pd
from playwright.async_api import async_playwright, Playwright
from bs4 import XMLParsedAsHTMLWarning
from bs4.element import NavigableString
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


BARGRAPH_PATH = Path(
    r"C:\Users\Micah\Documents\CodeMe\mor_cms-1\backend\tableau_bar.svg"
)


class HTMLPDFReporter:
    def __init__(
        self,
        name: str,
        html: str,
        sameday_rate: float,
        approval_rate: float,
        metrics_text: list[str],
        body_html: Optional[str] = None,
    ) -> None:
        self.name = name
        # self.html = html
        self._html = None
        self.bs = bs4.BeautifulSoup(html, "html.parser")
        self.sameday_rate = sameday_rate
        self.approval_rate = approval_rate
        self.metrics_text = metrics_text
        self.highlights_html = body_html

    @property
    def html(self):
        if self._html is None:
            return self.bs.prettify()
        else:
            self._html = self.bs.prettify()
            return self._html

    @html.setter
    def html(self, value):
        self._html = value

    @property
    @cache
    def pdf_path(self):
        return Path(f"./htmloutput/{self.name}.pdf")

    async def run_async_playwright(self):
        async with async_playwright() as p:
            await self.async_create_pdf(p)

    def sync_playwright_wrapper(self):
        asyncio.run(self.run_async_playwright())

    async def async_create_pdf(self, playwright: Playwright):
        browser = playwright.chromium
        browser = await browser.launch()
        context = await browser.new_context(base_url=Path("./").as_posix())
        page = await context.new_page()
        approval_graph, tat_graph = create_charts(self.sameday_rate, self.approval_rate)
        approval_b64 = base64.b64encode(approval_graph.encode("utf-8")).decode("utf-8")
        tat_b64 = base64.b64encode(tat_graph.encode("utf-8")).decode("utf-8")
        approval_img = self.bs.find("img", {"id": "approval"})
        # print(approval_img)
        # approval_img.string = approval_graph

        # approval_img["src"] = approval_graph
        tat_img = self.bs.find("img", {"id": "tat"})
        # tat_img.string = tat_graph
        approval_img["src"] = f"data:image/svg+xml;base64,{approval_b64}"
        # approval_img.replace_with(bs4.BeautifulSoup(approval_graph, "html.parser"))
        # tat_img.replace_with(bs4.BeautifulSoup(tat_graph, "html.parser"))
        tat_img["src"] = f"data:image/svg+xml;base64,{tat_b64}"
        textheadings = self.bs.select(".items")
        self.populate_metrics_div(self.metrics_text)
        if self.highlights_html:
            print(self.highlights_html)
            highlights_cont = self.bs.select_one(".top")
            if highlights_cont:
                highlights_cont.replace_with(
                    bs4.BeautifulSoup(self.highlights_html, "html.parser")
                )
            else:
                raise ValueError("Highlights not found")
        await page.set_content(self.html)
        await page.wait_for_load_state("load")
        await page.pdf(
            path=Path(
                f"./htmloutput/{self.pdf_path}",
            ),
            print_background=True,
            format="Letter",
        )
        print(self.pdf_path)
        return self.pdf_path

    def populate_metrics_div(self, metrics_data: list[str]):
        container = self.bs.select_one(".compressed-text")
        if container:
            container.clear()
            for item in metrics_data:
                ele = self.bs.new_tag("p")
                item = str(item)
                if " - " in item:
                    name, number = item.split("-")
                    ele.insert(0, NavigableString(name))
                    b = self.bs.new_tag("b", string=NavigableString(number))
                    ele.append(b)
                else:
                    ele.insert(0, NavigableString(item))
                container.append(ele)
        else:
            raise ValueError("Container ele not found.")


def create_charts(same_day_rate: float, approval_rate: float):
    approval_graph = BytesIO()
    tat_graph = BytesIO()
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
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    plt.pie(
        (
            same_day_rate * 100,
            100 - float(same_day_rate) * 100,
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
        f"Completed Within 24 Hours:\n{same_day_rate:.1%}",
        **textbox_kwargs,
    )
    p = plt.gcf()
    my_circle = plt.Circle((0, 0), 0.55, color="white")
    p.gca().add_artist(my_circle)
    plt.savefig(tat_graph, format="svg")
    tat_graph.seek(0)
    fig.clear()
    ax.clear()
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 6), dpi=300, layout="constrained")
    # inscope_requests = data[key]["InScope_Requests"]
    # handled_msgs = data[key]["Handled_Messages"]

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
    approval_graph.seek(0)
    return Charts(
        approval_graph.read().decode("utf-8"), tat_graph.read().decode("utf-8")
    )


class Charts(NamedTuple):
    approval_graph: str
    tat_graph: str


# metrics = [
#     int(result[key]["Decisions"]),
#     f"{result[key]['Approval_Rate'] * 100:.1f}%",
#     f"{result[key]['Same_Day_Rate'] * 100:.1f}%",
# ]


keys = [
    "Same_Day_Rate",
    "InScope_Requests",
    "Handled_Messages",
    "Decisions",
    "Approval_Rate",
]


class MonthExport(TypedDict):
    Same_Day_Rate: float
    InScope_Requests: int
    Handled_Messages: int
    Decisions: int
    Approval_Rate: float


def get_metrics_text(tableau_data: pd.DataFrame, dept_name: str):
    metrics = [
        f"{tableau_data.loc[dept_name, 'Decisions'].values[0]:,}",
        f"{tableau_data.loc[dept_name, 'Approval_Rate'].values[0]:.1%}",
        f"{tableau_data.loc[dept_name, 'Same_Day_Rate'].values[0]:.1%}",
    ]
    metrics_labels = [
        "Medication refills addressed - ",
        "Percentage of refills handled by Refill Center - ",
        "Percentage of encounters with 24H Turnaround Time - ",
    ]
    metrics_text = [str(x) + str(y) for x, y in zip(metrics_labels, metrics)]
    return metrics_text
