from ast import Tuple
from pathlib import Path
from bs4 import XMLParsedAsHTMLWarning, BeautifulSoup as bs
import warnings


from charts import create_dual_bar_chart

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def fill_table(html: bs, data: list[list[str]], selector="#deferral-table"):
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
    html = parse_html_body(
        r"C:\Users\Micah\Documents\CodeMe\mdReportCards2026\templateBeta.html"
    )
    fill_table(html, [["1", "2", "3"], ["1", "2", "3"]], "#deferral-table")
    fill_personal_stats(html, {"a": "123", "b": "345"})
    svg = create_dual_bar_chart(
        [200, 1200], ["Labs", "Appts"], "Care Gaps", Path("dualbar2.svg")
    )
    insert_chart(html, svg, ".image-container")
    insert_name(html, "gingerCuz")
    export_path = Path("tableblah.html")
    with open(export_path, "w") as file:
        file.write(html.prettify())
    print(export_path.absolute())
