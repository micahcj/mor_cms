from ast import Tuple
from dataclasses import asdict, dataclass
from pathlib import Path
from sys import platform
import time
from typing import Collection
from bs4 import XMLParsedAsHTMLWarning, BeautifulSoup as bs
import warnings


from charts import create_dual_bar_chart

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


@dataclass
class OverviewStats:
    refills: int
    sameday: str
    approval: str
    staff: str

    @property
    def dict(self):
        return asdict(self)


def fill_table(html: bs, data: Collection[Collection[str]], selector="#deferral-table"):
    table = html.select_one(selector)
    assert table is not None
    for deferral_reason in data:
        tr = html.new_tag("tr")
        for i, entry in enumerate(deferral_reason):
            td = html.new_tag("td", string=entry)
            if i > 0:
                td["class"] = "center"
            tr.append(td)
        table.append(tr)
    return html


def fill_overview(html: bs, data: OverviewStats):
    for id, value in data.dict.items():
        ele_selector = f"#{id}"
        ele = html.select_one(ele_selector)
        try:
            assert ele is not None
            ele.string = str(value)
        except AssertionError as e:
            print(f"{e} --> {id}:{value}")

    return html


def fill_personal_stats(
    html: bs, data: dict[str, str], selector: str = ".overview-list"
):
    ul = html.select_one(".overview-list")
    assert ul is not None
    for key, value in data.items():
        li = html.new_tag("li")
        div = html.new_tag("div")
        div["class"] = "li-box"
        label_ele = html.new_tag("span", string=key)
        div.append(label_ele)
        val_ele = html.new_tag("span", string=value)
        val_ele["class"] = "value"
        div.append(val_ele)
        li.append(div)
        ul.append(li)


def parse_html_body(template: Path | str):
    with open(template, encoding="utf8") as file:
        txt = file.read()
        html = bs(txt, "html.parser")
        file.close()
    return html


def insert_chart(html: bs, markup: str, selector=".image-container"):
    container = html.select_one(selector)
    assert container is not None
    container.clear()
    svg = bs(markup, features="html.parser")
    container.append(svg)


def insert_name(html: bs, name: str, selector="#name"):
    ele = html.select_one(selector)
    assert ele is not None
    ele.string = name


if __name__ == "__main__":
    template_path = (
        Path("/Users/micah/Documents/CodeMe/mdreports2026/templateBeta2.html")
        if platform == "darwin"
        else Path(
            r"C:\Users\Micah\Documents\CodeMe\mdReportCards2026\templateBeta.html"
        )
    )
    html = parse_html_body(template_path)
    fill_table(
        html,
        ((str(x) for x in range(x, x + 3)) for x in range(1, 4)),
        "#deferral-table",
    )  # type: ignore
    # fill_table(html, [["1", "2", "3"], ["1", "2", "3"]], "#deferral-table")
    # fill_personal_stats(html, {"a": "123", "b": "345"})
    stats = OverviewStats(1240, "99%", "55%", "4%")
    fill_overview(html, stats)
    svg = create_dual_bar_chart(
        [200, 1200], ["Labs", "Appts"], "Care Gaps", Path("dualbar2.svg")
    )
    insert_chart(html, svg, ".image-container")
    for name in ["1", "2", "3"]:
        insert_name(html, name)
        export_path = Path("tableblah_mac.html")
        with open(export_path, "w") as file:
            file.write(html.prettify())
        # print(export_path.absolute())
        # time.sleep(5)
