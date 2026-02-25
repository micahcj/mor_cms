import os
import json
import sys
from typing import Literal, Optional
import aiofiles
import pandas as pd
from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString
from pprint import pprint
from icecream import ic
from functools import cache
import asyncio
from playwright.async_api import async_playwright, Playwright
from playwright.sync_api import sync_playwright, Playwright as PlayWrightSync
from pathlib import Path


class PDFReporter(object):
    def __init__(
        self,
        name: str,
        json_file: Optional[str],
        approval_graph: Path,
        tat_graph: Path,
        care_gaps: bool = False,
        html_template: Optional[Path] = None,
        html_string: Optional[str] = None,
    ) -> None:
        self.name = name
        self.approval_graph = approval_graph
        self.tat_graph = tat_graph
        self.json_file = json_file or None
        self.care_gaps: bool = care_gaps
        self.html_template = html_template
        if html_string:
            self.html = self.parse_raw_html(html_string)
        else:
            if not html_template:
                raise ValueError("No html provided.")
            self.html = self.parse_html_file(html_template)
        self.html_report = f"{self.name}.html"
        self.pdf_report = f"{self.name}.pdf"
        self.json_obj: dict = {}

    def parse_raw_html(self, txt: str):
        return bs(txt, "html.parser")

    def parse_html_file(self, template: Path):
        with open(template, encoding="utf8") as file:
            txt = file.read()
            html = bs(txt, "html.parser")
            file.close()
        return html

    def sync_create_report(
        self,
        populate_content: bool = False,
        template_path: Optional[Path] = None,
        new_text=False,
    ):
        if template_path is None:
            if populate_content:
                template_path = Path("./html_report_content.html")
                self.html = self.parse_html_file(template_path)
                print("specialZ")
            else:
                template_path = Path("./html_report.html")
                print("self.name is the name")
        else:
            self.html = self.parse_html_file(template_path)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.add_style_tag(path=Path("./content/chatstyle2.css"))
            filepath = (
                # f"file://{rf'C:\Users\Micah\Documents\CodeMe\MOR-Script\{self.name}.html'}"
                Path(rf"C:\Users\Micah\Documents\CodeMe\MOR-Script\{self.name}.html")
                if sys.platform == "win32"
                else Path(f"{self.name}.html").resolve().as_uri()
            )
            print(filepath.as_uri())
            page.goto(filepath.as_posix(), wait_until="load")

            # page.reload(wait_until="domcontentloaded")
            page.pdf(
                path=Path(f"./htmloutput/{self.pdf_report}"),
                prefer_css_page_size=True,
                # width="8in",
                # height="9in",
                # scale=0.95,
                print_background=False,
                # )
                format="Letter",
            )
            print(Path(f"./htmloutput/{self.pdf_report}").resolve().as_posix())
            browser.close()

    def create_report(
        self,
        populate_content: bool = False,
        template_path: Optional[Path] = None,
        new_text=False,
        scale: Optional[float] = 0.95,
    ):
        """redefine or rename template_path because I don't think I Know what it actually does. want it to be the path to the html template. that's all. but it may the output"""

        """Adds the content specified to the textheaders divs. 
            
            special_content: bool = content other than the 3 text headings to be entetered. Will use template with NO TEXT HEADERS IN BODY.
            template_path: str = path to html template. Will be used with no regard to special_content."""
        if scale is None:
            scale = 0.95
        if template_path is None:
            if populate_content:
                template_path = Path("./html_report_content.html")
                self.html = self.parse_html_file(template_path)
                print("specialZ")
            else:
                template_path = Path("./html_report.html")
                print("self.name is the name")
        else:
            self.html = self.parse_html_file(template_path)

        async def run_html(playwright:Playwright,html:str):
            browser = playwright.chromium
            browser = await browser.launch()
            context = await browser.new_context(base_url=Path("./").as_posix())
            page = await context.new_page()
            await page.set_content(html)

        async def run(playwright: Playwright):
            browser = playwright.chromium
            browser = await browser.launch()
            context = await browser.new_context(base_url=Path("./").as_posix())
            page = await context.new_page()

            filepath = (
                # f"file://{rf'C:\Users\Micah\Documents\CodeMe\MOR-Script\{self.name}.html'}"
                Path(rf"C:\Users\Micah\Documents\CodeMe\MOR-Script\{self.name}.html")
                if sys.platform == "win32"
                else Path(f"{self.name}.html")  # .resolve().as_uri()
            )
            # await page.goto(
            #     f'file://{rf"C:\Users\Micah\Documents\CodeMe\MOR-Script\{self.name}.html"}'
            # )
            filelink = filepath.resolve().as_uri()
            print(filelink)
            # await page.goto(filelink, wait_until="load")
            await page.add_style_tag(path=Path("./content/styles.css"))
            await page.wait_for_load_state("load")
            # await page.emulate_media(media="screen")
            dimensions = await page.evaluate("""
            () => {
                const body = document.body;
                const html = document.documentElement;

                const width = Math.max(
                    body.scrollWidth, body.offsetWidth, html.clientWidth, html.scrollWidth, html.offsetWidth
                );
                const height = Math.max(
                    body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight
                );

                return { width, height };
            }
            """)

            # Convert pixels to inches
            width_in = f"{dimensions['width'] / 96}in"
            height_in = f"{dimensions['height'] / 96}in"
            await page.pdf(
                path=Path(f"./htmloutput/{self.pdf_report}"),
                # prefer_css_page_size=True,
                # width="8in",
                # height=height_in,
                # width=width_in,
                # height="11in",
                scale=scale,
                margin={
                    "top": "0.5in",
                    "bottom": "0.5in",
                    "left": "0.5in",
                    "right": "0.5in",
                },
                print_background=True,
                # )
                format="Letter",
            )
            print(Path(f"./htmloutput/{self.pdf_report}").resolve().as_posix())

        async def playwright_helper():
            async with async_playwright() as playwright:
                await run(playwright)

        def insert_tag(tag: str, content):
            element = self.html.new_tag(tag)
            element.insert(0, NavigableString(str(content)))
            div1.insert(0, element)

        def json_traversal(obj: dict | list):
            if isinstance(obj, list):
                for item in obj:
                    insert_tag("p", item)
            elif isinstance(obj, dict):
                for key in obj.keys():
                    item = obj[key]
                    insert_tag("p", key)
                    json_traversal(item)
            else:
                insert_tag("p", obj)

        print(self.html.prettify())
        approval_img = self.html.find("img", {"id": "approval"})
        # approval_img = self.html.find('#approval')
        approval_img["src"] = self.approval_graph
        tat_img = self.html.find("img", {"id": "tat"})
        tat_img["src"] = self.tat_graph
        textheadings = self.html.select(".items")
        # keys = tuple(self.json_obj.keys())
        # if keys[0] == 'content':
        # #     '''delete the textheadings (or grab another template page -- probably better
        # #     -- make it a param:special_content:Bool = False. )'''
        #     print("key is 'content'")

        if new_text:
            self.json_file = f"./content/content-{self.name}.json"

            container = self.html.select_one(".content")
            # test_img = self.html.new_tag("img")
            # test_img['src'] = "./content/cj.jpeg"
            # for child in container.contents:
            #     print(child)
            """going forward with idea that it will be empty."""
            textbox = self.html.select_one(".metrics-box")
            # print(self.json_obj)
            # container.append(test_img)
            for key in self.json_obj:
                div1 = self.html.new_tag("div")
                div2 = self.html.new_tag("div")
                div2["class"] = "compressed-text"
                if isinstance(self.json_obj, dict):
                    for key in self.json_obj.keys():
                        val = self.json_obj[key]
                        if isinstance(val, dict):
                            nested_key = list(val.keys())[0]
                            item = val[nested_key]
                        else:
                            # nested_key = item = val
                            header = self.html.new_tag("p")
                            header["class"] = "text-heading"
                            header.insert(0, NavigableString(key))
                            div1.append(header)
                            # if nested_key == 'text':
                            #     element = self.html.new_tag("h2")
                            #     element.insert(0,NavigableString(item))
                            #     div1.insert(0,element)
                            # elif nested_key ==  'img':
                            #     element = self.html.new_tag("img")
                            #     element['src'] = item
                            # val is a list/array
                            for item in val:
                                element = self.html.new_tag("p")
                                item = str(item)
                                if " - " in str(item):
                                    b = self.html.new_tag("b")
                                    texts = item.split("-")
                                    element.insert(0, NavigableString(texts[0] + "-"))
                                    if (len(str(texts[1]).strip()) > 3) and (
                                        "%" not in texts[1]
                                    ):
                                        texts[1] = (
                                            str(texts[1])[:-3]
                                            + ","
                                            + str(texts[1])[-3:]
                                        )
                                    b.insert(0, NavigableString(texts[1]))
                                    element.insert(1, b)
                                else:
                                    element.insert(len(header), NavigableString(item))
                                div2.insert(len(div1), element)
                                # element.insert(0,NavigableString(item))
                                # div1.insert(0,element)
                            # else:
                            #     div1.insert(0,NavigableString(str(val)))
                            textbox.insert(0, div1)
                            textbox.insert(1, div2)
                else:
                    val = self.json_obj
                    if isinstance(val, list):
                        for item in val:
                            element = self.html.new_tag("p")
                            element.insert(0, NavigableString(str(item)))
                            div1.insert(0, element)
                    else:
                        item = str(val)
                        element = self.html.new_tag("p")
                        element.insert(0, NavigableString(str(item)))
                        div1.insert(0, element)
                    container.append(div1)
        else:
            container = self.html.select(".textbox")
            for i, header_tag in enumerate(textheadings):
                if isinstance(self.json_obj, dict):
                    textme = list(self.json_obj.keys())[i]
                else:
                    textme = self.json_obj[i]
                # pprint(textme)
                for txt in textme:
                    li = self.html.new_tag("li")
                    if isinstance(txt, dict):
                        li.insert(0, tuple(txt.keys())[0])
                        ul = self.html.new_tag("ul")
                        for item in txt[tuple(txt.keys())[0]]:
                            subli = self.html.new_tag("li")
                            subli.insert(0, NavigableString(item))
                            ul.append(subli)
                        li.append(ul)
                    else:
                        li.insert(0, NavigableString(txt))
                    header_tag.append(li)

        options = {
            "page-size": "Letter",
            "print-media-type": "",
            "allow": "./",
            "margin-top": "0.75in",
            "margin-right": "0.75in",
            "margin-bottom": "0.75in",
            "margin-left": "0.75in",
            "encoding": "UTF-8",
            "enable-local-file-access": "",
            "enable-internal-links": "",
            "images": "",
            # "user-style-sheet": Path("./content/styles.css"),
            "user-style-sheet": Path("./content/chatstyle.css"),
        }
        with open(self.html_report, "w") as output:
            output.write(self.html.prettify(formatter="html5"))
            output.close()
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(playwright_helper())
        asyncio.run(playwright_helper())
        # await playwright_helper()

    # def test(self):
