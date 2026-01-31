import argparse
from ast import arg
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, NamedTuple, Optional

import icecream
from numpy import sort
from pandas import to_numeric
from data_utils import get_departments, parse_date, DepartmentKeys
import pandas as pd
import datetime as dt
from pprint import pprint
from sys import platform, argv
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from html_utils import create_report_pdf
from html_utils2 import get_template_path


args_n = len(argv)
args = None
use_args = False
parser = ArgumentParser()


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "1", "y"):
        return True
    elif v.lower() in ("no", "false", "f", "0", "n"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


@dataclass
class Args(Namespace):
    mode: Optional[Literal["multi", "single"]] = "multi"
    depts: Optional[str] = None
    sheets: Optional[str] = None
    export_data: bool = True
    export_pdf: bool = True
    path: Optional[Path] = None
    scale: Optional[float] = None

    @classmethod
    def from_namespace(cls, ns: Namespace) -> "Args":
        return cls(**vars(ns))


if args_n > 1:
    use_args = True
    parser.add_argument("mode", nargs="?", default="multi")
    parser.add_argument("depts", nargs="?", default=None)
    parser.add_argument("sheets", nargs="?", default=None)
    parser.add_argument("export_data", nargs="?", type=str2bool, default=True)
    parser.add_argument("export_pdf", nargs="?", type=str2bool, default=True)
    parser.add_argument("path", nargs="?", type=Path, default=None)
    parser.add_argument("scale", nargs="?", type=float, default=None)
    args = Args.from_namespace(parser.parse_known_args()[0])

department_colname = "Department"
rational_colname = "Rationale for Refill"
medproblems_colname = "Med Problems Grouped"
pharmreview_colname = "Requires Appointment"
appt_colname = "Requires Appointment"
lab_colname = "Requires Labs"
msgsrc_colname = "Message Source"
data_columns = [
    department_colname,
    rational_colname,
    medproblems_colname,
    pharmreview_colname,
    appt_colname,
    msgsrc_colname,
]


medproblem_keys = [
    "Allergy or intolerance",
    "Clarification of medication (Rx) details",
    "Drug-disease interaction",
    "Drug-drug interaction",
    "Due for refill >6 months ago",
    "ED/Hospital Visit since last OV with provider",
    "Med affordability",
    "Medication outside of protocol",
    "New or recently adjusted medication",
    "No active prescription written by provider",
    "Non-participating provider",
    "Other ",
    "Patient not seen by provider within 15 months",
    "Required labs abnormal",
    "Required labs outdated",
    "Required vitals abnormal",
    "Required vitals outdated",
]


# TableauTable = NamedTuple(
#     "TableauTable",
#     [
@dataclass
class TableauTable:
    Month: str
    Messages: int
    Decisions: int
    Approval_Rate: float
    Message_Reduction_Rate: float
    Handled_Messages: int
    InScope_Requests: int
    Routes: int
    Messages_Routed_Rate: float
    Defers: int
    Messages_Deferred_Rate: float
    Defers_With_Route: int
    Defers_With_Route_Rate: float
    Appts: int
    Appts_Inclusive: int
    Labs: int
    Labs_Inclusive: int
    Same_Day: int
    Same_Day_Rate: float
    Mean_Message_Age: float
    Median_Message_Age: float
    Mode_Message_Age: float
    Staff_Messages: int
    Staff_Messages_Rate: float
    InScope_Rate: float
    BARRA_Approve: float
    BARRA_QuickDC: float
    BARRA_Defer: float
    BARRA_Route: float
    # Handled_By_Decision: float
    # InScope_By_Decisions:float

    def to_dict(self):
        return asdict(self)


def gather_turnaround_time(
    delta: float, sent_time: dt.datetime, form_time: dt.datetime
):
    if delta < 1:
        return 1
    if sent_time.weekday() in {4, 5, 6}:
        if form_time.weekday() in {4, 5, 6}:
            return 1
        if (sent_time.hour >= 17) and (form_time.weekday() == 1):
            return 1
    return 0


def get_decisions(barra: str):
    if "^" in str(barra):
        return barra.count("^") + 1
    if pd.notna(barra):
        return 1
    return 0


def preprocess_df(df: pd.DataFrame):
    df.loc[::, "senttime"] = df["Sent Time"].apply(parse_date)
    df.loc[::, "formtime"] = df["Earliest Form Time"].apply(parse_date)
    df.loc[::, "delta"] = pd.to_timedelta((df["formtime"] - df["senttime"])).dt.days
    # df.loc[::, "delta"] = df["delta"].dt.days
    df.loc[::, "sameday"] = df.apply(
        lambda row: gather_turnaround_time(
            row["delta"], row["senttime"], row["formtime"]
        ),
        axis=1,
    )
    df.loc[::, "decisions"] = df[rational_colname].apply(get_decisions)
    df.loc[::, "Approval"] = (
        df[rational_colname].str.contains("Approve", case=False, na=False).astype(int)
    )
    df.loc[::, "Handled"] = (
        df[rational_colname]
        .str.contains("Approve|Quick", regex=True, case=False, na=False)
        .astype(int)
    )
    df.loc[::, "In Scope"] = (
        ~df[rational_colname].str.contains("Route", case=False, na=False)
        & (df[rational_colname].notna())
    ).astype(int)
    df.loc[::, "Route"] = (
        df[rational_colname].str.contains("Route", case=False, na=False).astype(int)
    )
    df.loc[::, "Defer"] = (
        df[rational_colname].str.contains("Defer", case=False, na=False).astype(int)
    )
    df.loc[::, "Defer/Route"] = (
        df[rational_colname]
        .str.contains("(?=.*Defer)(?=.*Route).+", case=False, na=False)
        .astype(int)
    )
    df.loc[::, "Approve/Route"] = (
        df[rational_colname]
        .str.contains("Route|Approve|Quick", case=False, na=False)
        .astype(int)
    )
    df.loc[::, "Staff Message"] = (
        df[msgsrc_colname].str.contains("Staff", case=False, na=False).astype(int)
    )
    df.loc[::, "Null"] = pd.isna(df[rational_colname])
    for barra in ("Approve", "Quick", "Defer", "Route"):
        key = f"BARRA_{barra}"
        df.loc[::, key] = (
            df[rational_colname].str.contains(barra, case=False, na=False).astype(int)
        )
    return df


def compile_data(df: pd.DataFrame, month: str) -> TableauTable:
    msg_count = len(df)
    # print(msg_count)
    msg_count = df["Rationale CONCAT"].notna().sum()
    # print(msg_count)
    df = df.copy().dropna(subset="Rationale CONCAT")
    # print(len(df))

    def get_average(value: int | float) -> float | int:
        if msg_count == 0:
            return 0
        return value / msg_count

    mean_msg_age = df["delta"].mean(skipna=True) * 24
    median_msg_age = df["delta"].median(skipna=True) * 24
    mode_msg_age = df["delta"].mode(dropna=True).mean() * 24
    sameday_rate = get_average(df["sameday"].sum())
    staff_msg = df["Staff Message"].sum()
    staff_msg_rate = get_average(staff_msg)
    msgs_reduced = df["Handled"].sum()
    msg_reduction_rate = get_average(msgs_reduced)
    decisions = df["decisions"].sum()
    sameday: int = df["sameday"].sum(skipna=True)
    approvals: int = df["Handled"].sum(skipna=True)
    defers: int = df["Defer"].sum(skipna=True)
    defer_rate: float = get_average(defers)
    approve_route: float = df["Approve/Route"].sum(skipna=True)
    inscope: int = df["In Scope"].sum(skipna=True)
    inscope_rate = get_average(inscope)
    handled: int = df["Handled"].sum(skipna=True)
    handled_rate: float = handled / inscope if inscope > 0 else 0
    routes: int = df["Route"].sum(skipna=True)
    route_rate: float = get_average(routes)
    defer_route: int = df["Defer/Route"].sum(skipna=True)
    defer_route_rate: float = get_average(defer_route)
    staff_msgs: int | None = df.groupby("Message Source").size().get("Staff")  # type: ignore
    appts: int = df[appt_colname].sum(skipna=True)
    labs: int = df[lab_colname].sum(skipna=True)
    appts_inclusive: int = (
        df["Encounter CSN"]
        .loc[
            (
                df[medproblems_colname]
                .str.contains("Patient not seen by provider within 15 months", na=False)
                .fillna(False)
            )
            | (pd.to_numeric(df[appt_colname], errors="coerce") == 1)
        ]
        .nunique()
    )
    labs_inclusive: int = (
        df["Encounter CSN"]
        .loc[
            (
                df[medproblems_colname]
                .str.contains("labs outdated", na=False)
                .fillna(False)
            )
            | (pd.to_numeric(df[lab_colname], errors="coerce") == 1)
        ]
        .nunique()
    )
    if staff_msgs is None:
        staff_msgs = 0
    return TableauTable(
        month,
        msg_count,
        decisions,
        handled_rate,
        msg_reduction_rate,
        handled,
        inscope,
        routes,
        route_rate,
        defers,
        defer_rate,
        defer_route,
        defer_route_rate,
        appts,
        appts_inclusive,
        labs,
        labs_inclusive,
        sameday,
        sameday_rate,
        mean_msg_age,
        median_msg_age,
        mode_msg_age,
        staff_msg,
        staff_msg_rate,
        inscope_rate,
        *(
            df[f"BARRA_{x}"].sum(skipna=True)
            for x in ("Approve", "Quick", "Defer", "Route")
        ),
    )


def get_med_problems(key: str, df: pd.DataFrame):
    medproblems_colname = "Med Problems Grouped"
    n = len(df)
    medprob_col = df[medproblems_colname].astype(str).fillna("")
    count = medprob_col.str.contains(key, regex=False).sum()
    rate = 0
    if n > 0:
        rate = count / n
    rate_key = str(key) + " %"
    return {key: count, rate_key: float(f"{rate:.5f}")}


def aggregate_med_problems(df: pd.DataFrame, grouping_colname: str):
    medproblems_colname = "Med Problems Grouped"
    medprobs_coldata = df[medproblems_colname]
    interim_medprobs_keys = ("^").join(set(medprobs_coldata.astype(str))).split("^")
    medprob_keys = set(interim_medprobs_keys)
    medprob_keys = sorted(medprob_keys)

    for key in medprob_keys:
        df[key] = medprobs_coldata.str.contains(key, regex=False, na=False)
    medprobs_df = df.groupby([grouping_colname])[medprob_keys].agg(
        ["count", "mean", "sum"]
    )
    # print(medprobs_df)
    return medprobs_df


def compile_medproblems(df: pd.DataFrame):
    medprob_result = {}
    for k in medproblem_keys:
        for key, v in get_med_problems(k, df).items():
            medprob_result[key] = v
    return medprob_result


def filter_keys(dept_key, filter_list):
    if filter_list is None:
        return True
    return dept_key in filter_list


def by_provider(
    sheets: Optional[str | Iterable[str]] = None,
    filter: Optional[Iterable[DepartmentKeys]] = None,
    cumulative=True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    provider_col = "ENCOUNTER_PROVIDER"
    agg_rate = ["sum", "mean"]

    column_aggregates: dict[str, Any] = {
        "Staff Message": agg_rate,
        "decisions": ["count", "sum"],
        "Handled": agg_rate,
        "In Scope": agg_rate,
        "Route": agg_rate,
        "Defer": agg_rate,
        "Defer/Route": agg_rate + ["count"],
        "Null": agg_rate,
        "sameday": agg_rate,
        "delta": ["mean"],
    }
    if isinstance(sheets, str):
        sheets = [sheets]
    if platform == "win32":
        filepath = r"Y:\Backup\E\Reporting\Spreadsheets\Monthly\2025\Tableau2025.xlsx"
    else:
        filepath = "/Volumes/Space/Backup/E/Reporting/Spreadsheets/Monthly/2025/Tableau2025.xlsx"
    if sheets is None:
        months = (dt.datetime(2025, x, 1).strftime("%b") for x in range(1, 13))
        sheets = [x for x in months if x in pd.ExcelFile(filepath).sheet_names]
    aggregate_dfs = []

    for month in sheets:
        print(month)
        df_interim = pd.read_excel(filepath, month, engine="calamine")
        # df_interim = pd.read_pickle(filepath + ".pckl")
        df_interim = preprocess_df(df_interim)
        if cumulative is False:
            df_interim["month"] = month
        aggregate_dfs.append(df_interim)
    df = pd.concat(aggregate_dfs)
    print(
        "Sum",
        df[provider_col]
        .str.contains("ACHARYA, ANSHUL S.", na=False)
        # .astype(int, errors="ignore")
        .sum(),
    )
    if cumulative:
        agg_df = df.groupby(provider_col).agg(column_aggregates)
        medprobs_df = aggregate_med_problems(df, provider_col)
    else:
        agg_df = df.groupby([provider_col, "month"]).agg(column_aggregates)
        medprobs_df = aggregate_med_problems(df, (provider_col, "month"))
    # agg_df[("delta", "hours")] = df[("delta", "mean")] * 24
    # print(df)
    return (agg_df, medprobs_df)


def main_aggregate(
    sheets: str | Iterable[str],
    filter: Optional[Iterable[DepartmentKeys]] = None,
    template_path: str | Path = "html_templates/mor-2025-08-pc.html",
    export_data=True,
    export_pdf=True,
    scale: Optional[float] = None,
):
    extra_departments: dict[str, list] = {}
    if isinstance(sheets, str):
        sheets = [sheets]
    if platform == "win32":
        filepath = r"Y:\Backup\E\Reporting\Spreadsheets\Monthly\2025\Tableau2025.xlsx"
    else:
        filepath = "/Volumes/Space/Backup/E/Reporting/Spreadsheets/Monthly/2025/Tableau2025.xlsx"
    if sheets is None:
        months = (dt.datetime(2025, x, 1).strftime("%b") for x in range(1, 13))
        sheets = [x for x in months if x in pd.ExcelFile(filepath).sheet_names]
    if export_data:
        medproblems: dict[str, list] = {}
        tableau: dict[str, list] = {}
        names = []
    interim_dfs = [
        pd.read_excel(filepath, month, engine="calamine") for month in sheets
    ]
    col_name = "Aggregate"
    agg_df = pd.concat(interim_dfs)
    df = preprocess_df(agg_df)
    departments = get_departments(df[department_colname])
    if filter:
        if any(key not in departments.keys() for key in filter):
            raise KeyError(
                f"Key (group name) {filter} not in departments.",
                f"Keys present: {', '.join(list(departments.keys()))}",
            )
    extra_departments["Aggregate"] = departments["ReExtras"]
    for dept_key, departments in departments.items():
        if filter:
            if dept_key not in filter:
                continue
        if export_data:
            if dept_key not in names:
                names.append(dept_key)
        for item in (medproblems, tableau):
            if item.get(dept_key, False) is False:
                item[dept_key] = []
        departments = [str(x).upper() for x in departments]
        dept_df = df.loc[df[department_colname].isin(departments)].copy()
        # dept_df.columns = [month]
        dept_dict = asdict(compile_data(dept_df, col_name))
        dept_results = {dept_key: dept_dict}
        med_probs = compile_medproblems(dept_df)

        if export_data:
            interim_medprob = pd.DataFrame.from_dict(
                med_probs, orient="index", columns=[col_name]
            )
            interim_medprob.Name = dept_key
            medproblems[dept_key].append(interim_medprob)
            interim_tab = pd.DataFrame.from_dict(
                dept_dict,
                orient="index",
            )
            interim_tab.Name = dept_key
            tableau[dept_key].append(interim_tab)
    if export_data or export_pdf:
        print("Exporting:", *names, *sheets)
        data_dict = {"medproblems": medproblems, "tableau": tableau}
        for title, data in data_dict.items():
            data_concat = []
            print(data_dict)
            for dept, dfs in data.items():
                interim = pd.concat(dfs, axis=1)
                data_concat.append(interim)
                if isinstance(sheets, str):
                    sheet_str = sheets
                else:
                    sheet_str = str(sheets[0]) + str(sheets[-1])
                output_path = (
                    f"serviceline_output/{dept}-{title}-{sheet_str}-concat.xlsx"
                )
                keys = list(data.keys())
                idx = keys.index(dept)
                labels = keys[: idx + 1]
                result_df = pd.concat(data_concat, keys=labels)
                if export_pdf and title == "tableau":
                    agg = sum_df(result_df)
                    agg = pd.concat([pd.Series(col_name, ["Month"]), agg])
                    agg["Month"] = col_name
                    agg_dict = {
                        dept: {
                            k: v
                            for k, v in zip((str(x[1]) for x in agg.index), agg.values)
                        }
                    }
                    create_report_pdf(
                        dept, agg_dict, get_template_path(dept, template_path), scale
                    )
            if export_data:
                dept_str = "".join(filter) if filter else "ALL"
                if isinstance(sheets, str):
                    sheet_str = sheets
                else:
                    sheet_str = str(sheets[0]) + str(sheets[-1])
                output_path = (
                    f"serviceline_output/{title}-{sheet_str}-{dept_str}-concat.xlsx"
                )
                with pd.ExcelWriter(output_path, "xlsxwriter") as writer:
                    sheetname = "".join(sheets)
                    result_df.columns = [f"{sheets[0]}-{sheets[-1]}"]
                    result_df.to_excel(excel_writer=writer, sheet_name=sheetname)
                    wb = writer.book
                    ws = writer.sheets[sheetname]
                    percent_format = wb.add_format({"num_format": "0.00%"})
                    format_rows = [
                        i
                        for i, label in enumerate(result_df.index, 1)
                        if any(x for x in {"rate", "%"} if x in str(label).lower())
                    ]
                    for row in format_rows:
                        ws.set_row(row, None, percent_format)
                print(Path(output_path).absolute())


def main_multi(
    sheets: str | Iterable[str],
    filter: Iterable[DepartmentKeys] = None,
    template_path: str | Path = "html_templates/mor-2025-08-pc.html",
    export_data=True,
    export_pdf=True,
    scale: Optional[float] = None,
):
    extra_departments: dict[str, list] = {}
    if isinstance(sheets, str):
        sheets = [sheets]
    if platform == "win32":
        filepath = r"Y:\Backup\E\Reporting\Spreadsheets\Monthly\2025\Tableau2025.xlsx"
    else:
        filepath = "/Volumes/Space/Backup/E/Reporting/Spreadsheets/Monthly/2025/Tableau2025.xlsx"
    if sheets is None:
        months = (dt.datetime(2025, x, 1).strftime("%b") for x in range(1, 13))
        sheets = [x for x in months if x in pd.ExcelFile(filepath).sheet_names]
    if export_data:
        medproblems: dict[str, list] = {}
        tableau: dict[str, list] = {}
        names = []
    for month in sheets:
        print(month)
        df = pd.read_excel(filepath, month, engine="calamine")
        df = preprocess_df(df)
        departments = get_departments(df[department_colname])
        extra_departments[month] = departments["ReExtras"]
        for dept_key, departments in departments.items():
            if filter:
                if dept_key not in filter:
                    continue
            if export_data:
                if dept_key not in names:
                    names.append(dept_key)
            for item in (medproblems, tableau):
                if item.get(dept_key, False) is False:
                    item[dept_key] = []
            departments = [str(x).upper() for x in departments]
            dept_df = df.loc[df[department_colname].isin(departments)].copy()
            # dept_df.columns = [month]
            dept_dict = asdict(compile_data(dept_df, month))
            dept_results = {dept_key: dept_dict}
            med_probs = compile_medproblems(dept_df)

            if export_data:
                interim_medprob = pd.DataFrame.from_dict(
                    med_probs, orient="index", columns=[month]
                )
                interim_medprob.Name = dept_key
                medproblems[dept_key].append(interim_medprob)
                interim_tab = pd.DataFrame.from_dict(
                    dept_dict,
                    orient="index",
                )
                interim_tab.Name = dept_key
                tableau[dept_key].append(interim_tab)
    if export_data or export_pdf:
        print("Exporting:", *names, *sheets)
        data_dict = {"medproblems": medproblems, "tableau": tableau}
        for title, data in data_dict.items():
            data_concat = []
            for dept, dfs in data.items():
                interim = pd.concat(dfs, axis=1)
                data_concat.append(interim)
                if isinstance(sheets, str):
                    sheet_str = sheets
                else:
                    sheet_str = str(sheets[0]) + str(sheets[-1])
                output_path = (
                    f"serviceline_output/{dept}-{title}-{sheet_str}-concat.xlsx"
                )
                keys = list(data.keys())
                idx = keys.index(dept)
                labels = keys[: idx + 1]
                result_df = pd.concat(data_concat, keys=labels)
                if export_pdf and title == "tableau":
                    agg = sum_df(result_df)
                    agg = pd.concat([pd.Series(month, ["Month"]), agg])
                    agg["Month"] = month
                    agg_dict = {
                        dept: {
                            k: v
                            for k, v in zip((str(x[1]) for x in agg.index), agg.values)
                        }
                    }
                    # flat_index = [' '.join(map(str, indx)).strip() for indx in df.index]

                    # (flat_index.index(x) for x in flat_index if any({'rate','%'}) in x.lower())
                    create_report_pdf(
                        dept, agg_dict, get_template_path(dept, template_path), scale
                    )
            if export_data:
                dept_str = "".join(filter) if filter else "ALL"
                output_path = Path(
                    f"serviceline_output/{title}-{sheet_str}-{dept_str}-concat.xlsx"
                )
                if output_path.exists():
                    output_path = Path(
                        dt.datetime.now().strftime("%b%d-%H%M") + output_path.name
                    )
                with pd.ExcelWriter(output_path, "xlsxwriter") as writer:
                    # sheetname = "".join(sheets)
                    sheetname = get_sheetname(sheets)
                    result_df.columns = sheets
                    result_df.to_excel(excel_writer=writer, sheet_name=sheetname)
                    wb = writer.book
                    ws = writer.sheets[sheetname]
                    percent_format = wb.add_format({"num_format": "0.00%"})
                    # flat_index = [" ".join(map(str, indx)).strip() for indx in df.index]
                    format_rows = [
                        i
                        for i, label in enumerate(result_df.index, 1)
                        if any(x for x in {"rate", "%"} if x in str(label).lower())
                    ]
                    # indexes_to_format = (
                    #     i
                    #     for i, x in enumerate(df.index, 1)
                    #     if any(y in x.lower() for y in {"rate", "%"})
                    # )
                    for row in format_rows:
                        ws.set_row(row, None, percent_format)
                # result_df.to_excel(output_path)
                print(Path(output_path).absolute())


def sum_df(df: pd.DataFrame):
    sums = []
    means = []
    index = df.index
    interim_idx = df.index.get_level_values(1)
    index = df.index

    if "Month" in interim_idx:
        index = df.index.drop(index[interim_idx.get_loc("Month")])
    for x in index:
        if any(substr in str(x) for substr in {"%", "Rate"}):
            means.append(x)
        else:
            sums.append(x)
    agg = pd.Series(index=index, dtype="float64")
    if sums:
        agg.loc[sums] = (
            (df.loc[sums])
            .astype(float)  # , errors="ignore")
            .sum(axis=1, skipna=True, numeric_only=True)
        )
    if means:
        agg.loc[means] = (
            df.loc[means].astype(float).mean(axis=1, skipna=True, numeric_only=True)
        )
    return agg


def get_sheetname(sheets: str | list[str]) -> str:
    if isinstance(sheets, str):
        if len(sheets) > 10:
            return sheets[::10]
    return sheets[0] + sheets[-1]


if __name__ == "__main__":
    # use_args = True
    print(args)
    if use_args:
        if args:
            match args.mode:
                case "multi":
                    fn = partial(main_multi)
                case "single":
                    fn = partial(main_aggregate)
                case _:
                    raise ValueError(
                        f'Mode "{args.mode}" not valid. Select either "multi" or "single."'
                    )
            print("Args:", args)
            sheets = str(args.sheets)
            depts = args.depts if bool(args.depts) else None  # type: ignore
            # export = args.export_ == "True"
            if "," in str(sheets):
                sheets = sheets.split(",")
            # depts = str(args.depts)
            if args.sheets is None or args.sheets == "":
                sheets = None
            if depts:
                if "," in str(depts):
                    depts: Iterable[DepartmentKeys] = str(args.depts).split(",")  # type: ignore
                else:
                    depts = [depts]  # type: ignore
            icecream.ic(sheets, depts, args.path)
            # ic(args.path, args.export_data, args.export_pdf, args.scale)
            if args.path:
                fn(
                    sheets,
                    depts,
                    template_path=args.path,
                    export_data=args.export_data,
                    export_pdf=args.export_pdf,
                    scale=args.scale or 1,
                )
            else:
                fn(
                    sheets,
                    depts,
                    export_data=args.export_data,
                    export_pdf=args.export_pdf,
                    # scale=0.85,
                )
        else:
            raise ValueError("No args parsed.")
    else:
        sheets = ("Aug", "Sep")
        print(f"No args. Using default sheets: {', '.join(sheets)}")
        main_multi(sheets, "TOTAL")  # , "TOTAL,Cardiology")
