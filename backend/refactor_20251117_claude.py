from collections import defaultdict, namedtuple
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import asdict
from functools import partial
import os
from pathlib import Path
from pprint import pprint
from time import time
from timeit import timeit
from typing import Collection, NamedTuple, Optional, Set, Tuple
from unittest import result
from data_utils import get_departments, DepartmentKeys, timing
import pandas as pd
import datetime as dt
from sys import platform, argv
from argparse import ArgumentParser
from html_utils import create_report_pdf
from html_utils2 import get_template_path
from locked_utils import LockedRoster
from refactor_20251112 import (
    Args,
    compile_data,
    compile_medproblems,
    preprocess_df,
    department_colname,
    str2bool,
    sum_df as get_sum_df,
)

TEMPLATE_PATH = Path("html_templates/mor-2025-08-pc.html")
cores = os.cpu_count() or 6
locked_roster = LockedRoster()
print("Core count:", cores)


def compile_aggregate_data(
    sheets: Optional[str | Collection[str]],
    filter: Optional[Collection[DepartmentKeys] | str] = None,
    export_data=True,
    export_pdf=True,
    template_path: str | Path = "html_templates/mor-2025-08-pc.html",
    scale: Optional[float] = None,
) -> dict[str, pd.DataFrame]:
    filepath = _get_filepath()
    sheets = _normalize_sheets(sheets, filepath)
    colname = "Aggregate"
    # if export_data:
    medproblems: dict[str, list] = {}
    tableau: dict[str, list] = {}
    names = []
    df = _threaded_load_and_concat_sheets(filepath, sheets)
    # if export_data:
    # df.to_excel(f"{sheets[0]}{sheets[-1]}-concat-export.xlsx")
    departments = get_departments(df[department_colname])
    if filter:
        _validate_filter(filter, departments)
    extra_departments = {"Aggregate": departments["ReExtras"]}
    for dept_name, dept_list in departments.items():
        if filter and (dept_name not in filter):
            continue
        if export_data and (dept_name not in names):
            names.append(dept_name)
        _initialize_dept_data(medproblems, tableau, dept_name)
        dept_df = _get_group_dataframe(df, dept_list)
        tableau_dict_interim = asdict(compile_data(dept_df, colname))
        medprobs_interim = compile_medproblems(dept_df)

        if export_data:
            _store_department_results(
                medproblems,
                tableau,
                dept_name,
                medprobs_interim,
                tableau_dict_interim,
                colname,
            )
    return _export_results(
        medproblems,
        tableau,
        sheets,
        filter,
        export_data,
        export_pdf,
        colname,
        template_path,
        scale,
        "aggregate",
    )


def compile_provider_data(
    sheets: Optional[str | Collection[str]],
    export_data=True,
) -> dict[str, pd.DataFrame]:
    filepath = _get_filepath()
    sheets = _normalize_sheets(sheets, filepath)
    colname = "Aggregate"
    provider_colname = "Encounter Provider"
    # if export_data:
    medproblems: dict[str, list] = {}
    tableau: dict[str, list] = {}
    names = []
    df = _threaded_load_and_concat_sheets(filepath, sheets)
    providers = sorted(set(df[provider_colname]))
    for i, provider in enumerate(providers):
        _initialize_dept_data(medproblems, tableau, provider)
        prov_df = _get_group_dataframe(df, [provider], provider_colname)
        tableau_dict_interim = asdict(compile_data(prov_df, colname))
        medprobs_interim = compile_medproblems(prov_df)
        _store_department_results(
            medproblems,
            tableau,
            provider,
            medprobs_interim,
            tableau_dict_interim,
            colname,
        )
        if i % 50 == 0:
            print(*sheets, f"{(i + 1) / len(providers) * 100:.2f}%")
    return _export_results(
        medproblems,
        tableau,
        sheets,
        None,
        export_data,
        False,
        colname,
        None,
        None,
        "aggregate",
    )


class CompiledData(NamedTuple):
    sheet: str
    names: list[str]
    medproblems: dict[str, list]
    tableau: dict[str, list]


def _compile_thread_helper(
    filepath: Path,
    sheet: str,
    filter: list[str],
    names: list[str],
    medproblems: dict[str, list],
    tableau: dict[str, list],
    sheets: list[str],
    export_data: bool,
    # ) -> Tuple[str, list[str], dict[str, list], dict[str, list]]:
) -> CompiledData:
    df = _load_and_concat_sheets(filepath, [sheet])
    departments = get_departments(df[department_colname])
    for group_name, dept_list in departments.items():
        if filter and (group_name not in filter):
            continue
        if export_data and (group_name not in names):
            names.append(group_name)
        _initialize_dept_data(medproblems, tableau, group_name)
        dept_df = _get_group_dataframe(df, dept_list)
        tableau_dict_interim = asdict(compile_data(dept_df, sheet))
        medprobs_interim = compile_medproblems(dept_df)

        if export_data:
            _store_department_results(
                medproblems,
                tableau,
                group_name,
                medprobs_interim,
                tableau_dict_interim,
                sheet,
            )
    return CompiledData(sheet, names, medproblems, tableau)


def _threaded_provider_roster_helper(path: Path, sheets: list[str]):
    def process_provider_col(sheet: str) -> pd.Series:
        df = pd.read_excel(path, sheet_name=sheet, engine="calamine")
        if "ENCOUNTER_PROVIDER" in (str(col) for col in df.columns):
            print("Renaming 'ENCOUNTER_PROVIDER' column.")
            df.rename(
                columns={"ENCOUNTER_PROVIDER": "Encounter Provider"}, inplace=True
            )
            # locked_roster.add(df["Encounter Provider"])
        # return set(df["Encounter Provider"])
        locked_roster.df_dict[sheet] = df
        return df["Encounter Provider"]

    with ThreadPoolExecutor(cores) as executor:
        # futures = (
        #     executor.submit(
        #         process_provider_col,
        #         pd.read_excel(path, sheet_name=sheet, engine="calamine"),
        #     )
        #     for sheet in sheets
        # )
        results = executor.map(process_provider_col, sheets)
        # results = [future.result() for future in futures]
    # roster = set()
    for x in results:
        locked_roster.manual_roster.update(x)
    return locked_roster.manual_roster


def _compile_provider_thread_helper(
    filepath: Path,
    sheet: str,
    filter: list[str],
    names: list[str],
    medproblems: dict[str, list],
    tableau: dict[str, list],
    sheets: list[str],
    export_data: bool,
    # ) -> Tuple[str, list[str], dict[str, list], dict[str, list]]:
) -> CompiledData:
    provider_colname = "Encounter Provider"
    if not locked_roster:
        print(f"Loading sheets for the first time in {__name__}")
        df = _load_and_concat_sheets(filepath, [sheet])
    else:
        print("Loading sheet from locked_roster.df_dict.")
        df = preprocess_df(locked_roster.df_dict[sheet])
    # locked_roster.add(df[provider_colname])
    # providers = [(x, [x]) for x in sorted(set(df[provider_colname]))]
    # providers = [(x, [x]) for x in locked_roster.roster]
    # providers = [(x, [x]) for x in locked_roster.manual_roster]
    providers = sorted(locked_roster.manual_roster)
    for i, provider in enumerate(providers):
        if filter and (provider not in filter):
            continue
        if provider not in names:
            names.append(provider)
        _initialize_dept_data(medproblems, tableau, provider)
        prov_df = _get_group_dataframe(df, [provider], provider_colname)
        tableau_dict_interim = asdict(compile_data(prov_df, sheet))
        medprobs_interim = compile_medproblems(prov_df)

        _store_department_results(
            medproblems,
            tableau,
            provider,
            medprobs_interim,
            tableau_dict_interim,
            sheet,
        )
        if i % 50 == 0:
            print(
                sheet,
                f"{(i + 1) / len(providers) * 100:.2f}%",
                f"({len(providers)} total)",
            )
    return CompiledData(sheet, names, medproblems, tableau)


@timing
def compile_monthly_data(
    sheets: Optional[str | Collection[str]],
    filter: Optional[Collection[DepartmentKeys] | str] = None,
    export_data=True,
    export_pdf=True,
    template_path: str | Path = "html_templates/mor-2025-08-pc.html",
    scale: Optional[float] = None,
) -> dict[str, pd.DataFrame]:
    """Multithreaded approach"""
    filepath = _get_filepath()
    sheets = _normalize_sheets(sheets, filepath)
    title = "Monthly"
    if export_data:
        medproblems: dict[str, list] = {}
        tableau: dict[str, list] = {}
        names = []
        with ThreadPoolExecutor(cores) as executor:
            threads = [
                executor.submit(
                    _compile_thread_helper,
                    filepath,
                    month,
                    filter,
                    [],
                    {},
                    {},
                    sheets,
                    export_data,
                )
                for month in sheets
            ]
            results = [future.result() for future in threads]

        # medproblems = {
        #     k: v for result in results for k, v in result.medproblems.items()
        # }
        # tableau = {k: v for result in results for k, v in result.tableau.items()}
        medproblems = defaultdict(list)

        tableau = defaultdict(list)
        for result in results:
            for k, v in result.medproblems.items():
                medproblems[k].extend(v if isinstance(v, list) else [v])
            for k, v in result.tableau.items():
                tableau[k].extend(v if isinstance(v, list) else [v])

    return _export_results(
        medproblems,
        tableau,
        sheets,
        filter,
        export_data,
        export_pdf,
        title,
        template_path,
        scale,
        "monthly",
    )


@timing
def compile_monthly_provider_data(
    sheets: Optional[str | Collection[str]],
) -> dict[str, pd.DataFrame]:
    """Multithreaded approach"""

    filepath = _get_filepath()
    sheets = _normalize_sheets(sheets, filepath)
    title = "ProviderMonthly"
    print(title)
    # if export_data:
    roster = _threaded_provider_roster_helper(filepath, sheets)
    medproblems: dict[str, list] = {}
    tableau: dict[str, list] = {}
    names = []

    def worker(month):
        print("This", month)
        return _compile_provider_thread_helper(
            filepath,
            month,
            None,
            [],
            {},
            {},
            sheets,
            True,
        )

    with ThreadPoolExecutor(cores) as executor:
        # threads = [
        #     executor.submit(
        #         _compile_provider_thread_helper,
        #         filepath,
        #         month,
        #         None,
        #         [],
        #         medproblems,
        #         tableau,
        #         [month],
        #         True,
        #     )
        #     for month in sheets
        # ]
        results = list(executor.map(worker, sheets))
        # results = [future.result() for future in threads]
        # print(*(list(result.medproblems.values())
        #       [0][0].values for result in results))

    medproblems = defaultdict(list)

    tableau = defaultdict(list)

    for result in results:
        for k, v in result.medproblems.items():
            medproblems[k].extend(v if isinstance(v, list) else [v])
        for k, v in result.tableau.items():
            tableau[k].extend(v if isinstance(v, list) else [v])
    # medproblems = {k: v for result in results for k,
    #                v in result.medproblems.items()}
    # tableau = {k: v for result in results for k, v in result.tableau.items()}
    # pprint({k: v for k, v in tableau.items() if 'balamane' in str(k).lower()})
    return _export_results(
        medproblems,
        tableau,
        sheets,
        None,
        True,
        False,
        title,
        None,
        None,
        "monthlyProvider",
    )


@timing
def compile_monthly_data_SINGLE(
    sheets: Optional[str | Collection[str]],
    filter: Optional[Collection[DepartmentKeys] | str] = None,
    export_data=True,
    export_pdf=True,
    template_path: str | Path = "html_templates/mor-2025-08-pc.html",
    scale: Optional[float] = None,
):
    filepath = _get_filepath()
    sheets = _normalize_sheets(sheets, filepath)
    title = "Monthly"
    if export_data:
        medproblems: dict[str, list] = {}
        tableau: dict[str, list] = {}
        names = []
    with ThreadPoolExecutor(cores) as executor:
        for month in sheets:
            print(month)
            future = executor.submit(_load_and_concat_sheets(filepath, [month]))
            wait(future)
            df = future.result()
            departments = get_departments(df[department_colname])
            for dept_name, dept_list in departments.items():
                if filter and (dept_name not in filter):
                    continue
                if export_data and (dept_name not in names):
                    names.append(dept_name)
                _initialize_dept_data(medproblems, tableau, dept_name)
                dept_df = _get_group_dataframe(df, dept_list)
                tableau_dict_interim = asdict(compile_data(dept_df, month))
                medprobs_interim = compile_medproblems(dept_df)

                if export_data:
                    _store_department_results(
                        medproblems,
                        tableau,
                        dept_name,
                        medprobs_interim,
                        tableau_dict_interim,
                        title,
                    )
    _export_results(
        medproblems,
        tableau,
        sheets,
        filter,
        export_data,
        export_pdf,
        title,
        template_path,
        scale,
        "monthlySingle",
    )


def _get_filepath():
    if platform == "win32":
        return Path(r"Y:\Backup\E\Reporting\Spreadsheets\Monthly\2025\Tableau2025.xlsx")
    return Path(
        "/Volumes/Space/Backup/E/Reporting/Spreadsheets/Monthly/2025/Tableau2025.xlsx"
    )


def _normalize_str_input(string: str | Collection[str]):
    if string:
        if isinstance(string, str):
            if "," in string:
                return [str(x).strip() for x in string.split(",")]
            return [string]
        return string
    return string


def _normalize_sheets(sheets: Optional[str | Collection[str]], filepath: Path):
    if sheets:
        sheets = _normalize_str_input(sheets)
    else:
        months = (dt.datetime(2025, x, 1).strftime("%b") for x in range(1, 13))
        available_sheets = pd.ExcelFile(filepath, engine="calamine").sheet_names
        return [x for x in months if x in available_sheets]
    return list(sheets)


def _load_and_concat_sheets(
    filepath: Path, sheets: list[str], export_data: bool = False
):
    interim_dfs = []
    for month in sheets:
        print(month)
        interim_df = pd.read_excel(filepath, month, engine="calamine")
        if "ENCOUNTER_PROVIDER" in (str(col) for col in interim_df.columns):
            print("Renaming 'ENCOUNTER_PROVIDER' column.")
            interim_df.rename(
                columns={"ENCOUNTER_PROVIDER": "Encounter Provider"}, inplace=True
            )
        interim_dfs.append(interim_df)
    agg_df = pd.concat(interim_dfs)
    if export_data:
        output_path = Path("aggdf.xlsx")
        if output_path.exists():
            output_path = Path(
                f"aggdf-{dt.datetime.now().strftime('%Y%y%d-%H%M%S')}.xlsx"
            )
        agg_df.to_excel(output_path, engine="xlsxwriter")
        print("Big Agg DF", output_path.absolute())
    df = preprocess_df(agg_df)
    return df


def _threaded_load_and_concat_sheets(
    filepath: Path, sheets: list[str], export_data: bool = False
):
    def process_sheet(month: str):
        print(month)
        interim_df = pd.read_excel(filepath, month, engine="calamine")
        if "ENCOUNTER_PROVIDER" in (str(col) for col in interim_df.columns):
            # print("Renaming 'ENCOUNTER_PROVIDER' column.")
            interim_df.rename(
                columns={"ENCOUNTER_PROVIDER": "Encounter Provider"}, inplace=True
            )
        return interim_df

    interim_dfs = []
    with ThreadPoolExecutor(cores) as executor:
        # interim_df = [executor.submit(pd.read_excel,filepath, month, engine="calamine") for month in sheets]
        # interim_dfs.append(interim_df)
        interim_dfs = [executor.submit(process_sheet, month) for month in sheets]
        wait(interim_dfs)
        interim_dfs = [future.result() for future in interim_dfs]
    agg_df = pd.concat(interim_dfs)
    if export_data:
        print(f"Exporting aggregate df for {sheets}")
        output_path = Path("aggdf.xlsx")
        if output_path.exists():
            output_path = Path(
                f"aggdf-{dt.datetime.now().strftime('%Y%y%d-%H%M%S')}.xlsx"
            )
        start = time()
        agg_df.to_excel(output_path, engine="xlsxwriter")
        end = time()
        print("Big Agg DF", output_path.absolute(), f"took {end - start:.2f} seconds.")
    df = preprocess_df(agg_df)
    return df


def _validate_filter(filter, departments):
    if filter:
        filter = _normalize_str_input(filter)
        if any(key not in departments.keys() for key in filter):
            raise KeyError(
                f"Key (group name) {filter} not in departments."
                f"Keys present: {', '.join(list(departments.keys()))}",
            )


def _initialize_dept_data(medproblems, tableau, group_name: DepartmentKeys):
    for item in (medproblems, tableau):
        if item.get(group_name, False) is False:
            item[group_name] = []


def _get_group_dataframe(
    dataframe: pd.DataFrame, dept_list: list[str], colname=department_colname
):
    group = [str(x).upper() for x in dept_list]
    group_df = dataframe.loc[dataframe[colname].isin(group)].copy()
    return group_df


def _store_department_results(
    medproblems_data,
    tableau_data,
    dept_name,
    medprobs_interim,
    tableau_interim,
    colname: str,
):
    interim_medprob = pd.DataFrame.from_dict(
        medprobs_interim, orient="index", columns=[colname]
    )
    interim_medprob.Name = dept_name
    medproblems_data[dept_name].append(interim_medprob)
    interim_tab = pd.DataFrame.from_dict(
        tableau_interim, orient="index", columns=[colname]
    )
    interim_tab.Name = dept_name
    tableau_data[dept_name].append(interim_tab)


def _get_sheetname(sheets: str | list[str]) -> str:
    if not isinstance(sheets, str):
        sheets = sheets[0] + sheets[-1]
    if len(sheets) > 10:
        return sheets[::10]
    return sheets


# def _export_results(
#     medproblems: dict[str, list],
#     tableau: dict[str, list],
#     sheets,
#     filter,
#     export_data,
#     export_pdf,
#     title,
#     template_path,
#     scale,
#     mode=None,
# ):
#     print("Exporting:", set(list(medproblems.keys()) + list(tableau.keys())), *sheets)
#     data_dict = {"medproblems": medproblems, "tableau": tableau}
#     for title, data in data_dict.items():
#         data_list = []
#         for dept_name, df_list in data.items():
#             if len(df_list) > 1:
#                 interim = pd.concat(df_list, axis=1)
#             else:
#                 interim = df_list[0]
#             data_list.append(interim)
#         keys = list(data.keys())
#         idx = keys.index(dept_name)
#         labels = keys[: idx + 1]
#         print("Concatenating the interim data")
#         result_df = pd.concat(data_list, keys=labels)
#         if export_data:
#             _export_excel_file(result_df, title, sheets, filter)
#         if export_pdf and title == "tableau":
#             if not template_path:
#                 template_path = TEMPLATE_PATH
#             for dept in keys:
#                 _export_department_pdf(dept, result_df, title, template_path, scale)


def _export_results(
    medproblems: dict[str, list],
    tableau: dict[str, list],
    sheets,
    filter,
    export_data,
    export_pdf,
    title,
    template_path,
    scale,
    mode=None,
):
    # print(
    #     "Exporting:",
    #     set(list(medproblems.keys()) + list(tableau.keys())),
    #     *sheets,
    # )

    data_dict = {"medproblems": medproblems, "tableau": tableau}
    result_data = {}
    for title, data in data_dict.items():
        data_list: list[pd.DataFrame] = []
        labels: list[str] = []

        for dept_name, df_list in data.items():
            if not df_list:
                continue

            if len(df_list) > 1:
                interim = pd.concat(df_list, axis=1)
            else:
                interim = df_list[0]

            # # critical for concat(keys=...)
            # interim = interim.reset_index(drop=True)
            # interim.columns = interim.columns.map(
            #     lambda x: f"{x[0]}_{x[1]}"
            # )

            data_list.append(interim)
            labels.append(dept_name)

        if not data_list:
            continue
        # for df in data_list:
        #     if not df.index.is_unique:
        #         print(df.iloc[:10])
        #         raise Exception("shid")
        #     if not df.columns.is_unique:
        #         print(df.columns)
        #         print("Duplicate columns:",
        #               df.columns[df.columns.duplicated()])
        #         print(labels)
        #         raise Exception("Duplicate columns")
        #         print(df.iloc[:10])

        result_df = pd.concat(
            data_list,
            keys=labels,
            names=["department", "row"],
        )

        if export_data:
            _export_excel_file(result_df, title, sheets, filter, mode)

        if export_pdf and title == "tableau":
            if not template_path:
                template_path = TEMPLATE_PATH

            for dept in labels:
                _export_department_pdf(
                    dept,
                    result_df,
                    title,
                    template_path,
                    scale,
                )
        result_data[title] = result_df
    return result_data


def _export_department_pdf(
    dept_name: str,
    result_df: pd.DataFrame,
    colname: str,
    template_path: Path,
    scale: Optional[float],
):
    agg = get_sum_df(result_df)
    dept_source = agg.loc[dept_name]
    dept_data = {
        dept_name: {k: v for k, v in zip(dept_source.index, dept_source.values)}
    }
    if not template_path:
        template_path = TEMPLATE_PATH
    create_report_pdf(
        dept_name, dept_data, get_template_path(dept_name, template_path), scale
    )


def _export_excel_file(
    df: pd.DataFrame,
    title: str,
    sheets: list[str],
    filter=None,
    mode: Optional[str] = None,
):
    if not mode:
        mode = "aggregate"
    dept_str = "".join(filter) if filter else "ALL"
    sheet_str = sheets[0] if len(sheets) == 1 else f"{sheets[0]}{sheets[-1]}"
    # sheet_str = _get_sheetname(sheets)
    output_path = (
        f"serviceline_output/{mode}-{title}-{sheet_str}-{dept_str}-concat.xlsx"
    )
    new_columns = [sheet_str] if len(df.columns) == 1 else sheets
    with pd.ExcelWriter(output_path, "xlsxwriter") as writer:
        # sheetname = "".join(sheets)
        sheetname = _get_sheetname(sheets)
        # df.columns = pd.Index(data=new_columns)
        df.to_excel(excel_writer=writer, sheet_name=sheetname)
        _apply_excel_formatting(writer, sheetname, df)
    print(Path(output_path).absolute())


def _apply_excel_formatting(writer: pd.ExcelWriter, sheetname: str, df: pd.DataFrame):
    wb = writer.book
    ws = writer.sheets[sheetname]
    percent_format = wb.add_format({"num_format": "0.00%"})  # type: ignore
    format_rows = [
        i
        for i, label in enumerate(df.index, 1)
        if any(x for x in {"rate", "%"} if x in str(label).lower())
    ]
    for row in format_rows:
        ws.set_row(row, None, percent_format)


if __name__ == "__main__":
    args_n = len(argv)
    args = None
    use_args = False
    parser = ArgumentParser()

    if args_n > 1:
        use_args = True
        parser.add_argument("--mode", nargs="?", default="monthly")
        parser.add_argument("--depts", nargs="?", default=None)
        parser.add_argument("--sheets", nargs="?", default=None)
        parser.add_argument("--export_data", nargs="?", type=str2bool, default=True)
        parser.add_argument("--export_pdf", nargs="?", type=str2bool, default=False)
        parser.add_argument("--path", nargs="?", type=Path, default=None)
        parser.add_argument("--scale", nargs="?", type=float, default=None)
        args = Args.from_namespace(parser.parse_known_args()[0])
    if use_args and args:
        match str(args.mode).lower():
            case "monthly":
                fn = partial(compile_monthly_data)
            case "agg":
                fn = partial(compile_aggregate_data)
            case "aggregate":
                fn = partial(compile_aggregate_data)
            case "providerAggregate":
                fn = partial(compile_provider_data)
            case "providerMonthly":
                fn = partial(compile_monthly_provider_data)
            case _:
                raise ValueError(
                    f'Mode "{args.mode}" not valid. Select either "monthly" or "aggregate."'
                )
        print("Args:", args)
        departments = str(args.depts) if bool(args.depts) else None

        if bool(departments):
            if "," in departments:
                departments = departments.split(",")
            else:
                departments = [departments]

        if args.sheets in {None, ""}:
            sheets = None
        else:
            sheets = str(args.sheets)
            if "," in str(sheets):
                sheets = sheets.split(",")
        if "provider" in args.mode.lower():
            fn(
                sheets,
            )
        else:
            if args.path:
                fn(
                    sheets,
                    departments,
                    args.export_data,
                    args.export_pdf,
                    args.path,
                    args.scale or 1,
                )
            else:
                fn(
                    sheets,
                    departments,
                    args.export_data,
                    args.export_pdf,
                    scale=args.scale or 1,
                )
    # compile_aggregate_data(None, "PrimaryCare,OBGYN_2")
    else:
        month = dt.datetime.now().month - 1
        month_str = dt.datetime(2025, month, 1).strftime("%b")
        # compile_aggregate_data(month_str)
        compile_monthly_provider_data(["Jan", "Feb", "Mar"])
