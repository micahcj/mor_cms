from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional
from charts import create_bar_chart
from refactor_20251117_claude import (
    compile_aggregate_data,
    compile_monthly_data,
    compile_monthly_provider_data,
    compile_provider_data,
)
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json


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


def maintest():
    sheets = "Dec"
    mode = "provider"
    if mode != "provider":
        with ThreadPoolExecutor(2) as executor:
            agg_data, month_data = executor.map(
                lambda fn: fn(sheets, ["PrimaryCare", "TOTAL", "Cardiology"]),
                (compile_aggregate_data, compile_monthly_data),
            )
        tableau_month = month_data["tableau"]
        tableau_agg = agg_data["tableau"]
        # for data in (tableau_month, tableau_agg):
        #     print(data.loc["PrimaryCare"])
        tableau = tableau_month.loc["PrimaryCare"]
    else:
        with ThreadPoolExecutor(2) as executor:
            agg_data, month_data = executor.map(
                lambda fn: fn(sheets),
                (compile_provider_data, compile_monthly_provider_data),
            )
            tableau_month = month_data["tableau"]
            tableau_agg = agg_data["tableau"]
            tableau = tableau_month.loc["KLIBERT, DAVID M."]

    create_bar_chart(
        tableau.loc["Decisions"].values,
        tableau.loc["Month"].values,
        "Tableau",
        Path("../frontend/src/public/content/tableau_bar.svg"),
        "Refills",
    )
