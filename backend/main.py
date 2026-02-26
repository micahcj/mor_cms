import asyncio
from collections import defaultdict
from datetime import datetime
from io import BytesIO
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Collection, List, Literal, Optional

import pandas
from mor_library.charts import create_bar_chart, create_dual_bar_chart
# from mor_library.mdreport_html_utils import *

# from mor_library.mdreport_html_utils import get_care_gaps
from mor_library.refactor_20251117_claude import (
    compile_aggregate_data,
    compile_monthly_data,
    compile_monthly_provider_data,
    compile_provider_data,
)
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json
from pandas import DataFrame
from pydantic import BaseModel

from maybeold.html_report import PDFReporter
from maybeold.reporter import HTMLPDFReporter, MonthExport, get_metrics_text


TEMPLATE_PATH = Path(
    r"C:\Users\Micah\Documents\CodeMe\mor_cms-1\backend\202601_PrimaryCare.html"
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class Node:
    id: str
    text: str
    children: Optional[List["Node"]] = None


type IndentValue = Literal["Main", "Bullet", "Sub-Bullet"]


@dataclass
class TextObject:
    id: str
    text: str
    indentValue: IndentValue


@app.post("/api/highlights")
async def endpoint_highlights(request: Request):
    data = await request.json()
    print(*data.items(), sep="\n\n")
    return bool(data)


@app.post("/api/reload_barchart")
def reload_chart():
    maintest()


def get_care_gaps(df: pandas.DataFrame, name: str):
    data = df.loc[name]
    appts, labs = list(data.loc[["Appts", "Labs"]].values)
    return (appts, labs)


def create_care_gap_barchart(tableau_df: DataFrame, name: str):
    appts, labs = get_care_gaps(tableau_df, name)
    create_dual_bar_chart(
        [appts, labs],
        ["Appts", "Labs"],
        "Care Gaps",
        Path("../../mdReportCards2026/caregaps.svg"),
    )


type FunctionParam = Optional[str | list[str]]


def create_aggregate_report(
    depts: FunctionParam = ["PrimaryCare"], sheets: FunctionParam = None
):
    return compile_aggregate_data(
        sheets, depts, template_path="./html_templates/mor-2026-01-pc.html"
    )


def file_iterator(paths: Collection[Path]):
    for path in paths:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk


def zip_stream(paths: Collection[Path]):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=p)
    buffer.seek(0)
    yield from buffer


@app.get("/api/agg_report", response_class=StreamingResponse)
def agg_report(dept: str):
    print("agg report")
    return StreamingResponse(file_iterator(create_aggregate_report(dept)["paths"]))


class SheetRequest(BaseModel):
    year: int


def get_filepath(year: int):
    return Path(
        rf"Y:\Backup\E\Reporting\Spreadsheets\Monthly\{year}\Tableau{year}.xlsx"
    )


@app.post("/api/load_sheet", response_class=JSONResponse)
async def load_wb(request: Request, sheet: SheetRequest):
    # print(request.headers)
    if sheet.year not in {2024, 2025, 2026}:
        raise ValueError(f"Year {sheet.year} not valid for function.")
    filepath = Path(
        rf"Y:\Backup\E\Reporting\Spreadsheets\Monthly\{sheet.year}\Tableau{sheet.year}.xlsx"
    )

    sheetnames = [
        x
        for x in pandas.ExcelFile(filepath, engine="calamine").sheet_names
        if x
        in [datetime(sheet.year, month, 1).strftime("%b") for month in range(1, 13)]
    ]
    print(sheet.year, sheetnames, filepath.exists())
    return sheetnames


class UploadParams(BaseModel):
    year: int = 2026
    sheet: str = "Jan"
    depts: list[str] = ["PrimaryCare"]
    highlights_html: Optional[str] = None


@app.post("/api/upload_wb", response_class=JSONResponse)
def receive_file(
    request: Request,
    file: UploadFile,
    params: str = Form("{}"),
    # year: int = 2026,
    # sheet: str = "Jan",
    # depts: list[str] = ["PrimaryCare"],
    # highlights_html: Optional[str] = None,
):
    upload_params = UploadParams.model_validate_json(params)
    print("highlights_html", upload_params)
    print("fileepath", filepath := get_filepath(upload_params.year))
    filebytes = BytesIO(asyncio.run(file.read()))
    html = filebytes.getvalue().decode("utf-8")
    month_data = compile_monthly_data(
        upload_params.sheet, None, False, False, filepath=filepath
    )["tableau"]
    for dept in upload_params.depts:
        print(dept)
        dept_data = month_data.loc[dept]
        metrics = get_metrics_text(month_data, dept)
        sameday_rate = dept_data.loc["Same_Day_Rate"].values[0]
        approval_rate = dept_data.loc["Approval_Rate"].values[0]
        a = HTMLPDFReporter(
            "test",
            html,
            sameday_rate,
            approval_rate,
            metrics,
            upload_params.highlights_html,
        )
        a.sync_playwright_wrapper()
    print(bytes_len := len(filebytes.read()))
    return bytes_len


@app.post("/api/report")
def run_report(
    request: Request,
    params: str = Form("{}"),
):
    upload_params = UploadParams.model_validate_json(params)
    print("highlights_html", upload_params.highlights_html)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as template:
        html = template.read()
    print("fileepath", filepath := get_filepath(upload_params.year))
    month_data = compile_monthly_data(
        upload_params.sheet, None, False, False, filepath=filepath
    )["tableau"]
    for dept in upload_params.depts:
        print(dept)
        dept_data = month_data.loc[dept]
        metrics = get_metrics_text(month_data, dept)
        sameday_rate = dept_data.loc["Same_Day_Rate"].values[0]
        approval_rate = dept_data.loc["Approval_Rate"].values[0]
        a = HTMLPDFReporter(
            "test",
            html,
            sameday_rate,
            approval_rate,
            metrics,
            upload_params.highlights_html,
        )
        a.sync_playwright_wrapper()


def maintest():
    sheets = "Dec"
    mode = "provider"
    if mode != "provider":
        label = "PrimaryCare"
        with ThreadPoolExecutor(2) as executor:
            agg_data, month_data = executor.map(
                lambda fn: fn(sheets, ["PrimaryCare", "TOTAL", "Cardiology"]),
                (compile_aggregate_data, compile_monthly_data),
            )
        # tableau_month = month_data["tableau"]
        # tableau_agg = agg_data["tableau"]
        # # for data in (tableau_month, tableau_agg):
        # #     print(data.loc["PrimaryCare"])
        # tableau = tableau_month.loc["PrimaryCare"]
    else:
        label = "ANDERSON, DEREK J."
        with ThreadPoolExecutor(2) as executor:
            agg_data, month_data = executor.map(
                lambda fn: fn(sheets),
                (compile_provider_data, compile_monthly_provider_data),
            )
    tableau_month = month_data["tableau"]
    tableau_agg = agg_data["tableau"]
    tableau = tableau_month.loc[label]

    create_bar_chart(
        tableau.loc["Decisions"].values,
        tableau.loc["Month"].values,
        "Tableau",
        Path("../frontend/src/public/content/tableau_bar.svg"),
        "Refills",
    )
    create_care_gap_barchart(tableau_month, label)
