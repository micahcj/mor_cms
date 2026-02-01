from io import BytesIO
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Collection, List, Literal, Optional

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
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json
from pandas import DataFrame


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
    return compile_aggregate_data(sheets, depts, template_path="./html_templates/mor-2026-01-pc.html")


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
    print('agg report')
    return StreamingResponse(file_iterator(create_aggregate_report(dept)["paths"]))


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
