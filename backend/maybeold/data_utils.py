from functools import wraps
from time import time
import functools
from pathlib import Path
import re
import datetime as dt
from typing import Iterable, Literal
from csv import writer


DepartmentKeys = Literal[
    "OBGYN",
    "OBGYN_2",
    "PrimaryCare",
    "NLA",
    "NLACardiologyBatonRouge",
    "BR_PrimaryCare",
    "Cardiology",
    "TOTAL",
    "ReExtras",
]


def parse_date(string):
    if isinstance(string, dt.datetime):
        date = string
        return date
    else:
        if "-" in string:
            if 2 < len(string.split("-")[0]) >= 4:
                time_format = "%Y-%m-%d %H:%M:%S"
            elif [x for x in string].count(":") > 1:
                time_format = "%m-%d-%Y %H:%M:%S"
            elif len(string.split("/")[2]) <= 4:
                time_format = "%m-%d-%Y"
            else:
                time_format = "%m-%d-%Y %H:%M"
            date = dt.datetime.strptime(string, time_format)
        elif any(substring in string for substring in {"PM", "AM"}):
            time_format = "%m/%d/%Y %H:%M:%S %p"
            date = dt.datetime.strptime(string, time_format)
        else:
            if [x for x in string].count(":") > 1:
                time_format = "%m/%d/%Y %H:%M:%S"
            elif len(string.split("/")[2]) <= 4 or len([x for x in string]) < 11:
                time_format = "%m/%d/%Y"
            else:
                time_format = "%m/%d/%Y %H:%M"
            if "^" in string:
                dates = string.split("^")
                dates = [parse_date(x) for x in dates]
                date = min(dates)
            else:
                date = dt.datetime.strptime(string, time_format)
        return date


def get_departments(departments_source: Iterable) -> dict[DepartmentKeys, list[str]]:
    departments = {}
    departments["OBGYN"] = [
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 500",
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 400 ",
        "BAPC WOMENS GROUP ",
        "BAPC UROGYNECOLOGY ",
        "BNMC OBSTETRICS AND GYNECOLOGY ",
        "OCVC OBSTETRICS AND GYNECOLOGY",
        "BAPC WOMENS GROUP",
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 640",
        "BAPC UROGYNECOLOGY",
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 540",
        "KNMC OBSTETRICS AND GYNECOLOGY",
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 400",
        "KNMC OBSTETRICS AND GYNECOLOGY",
        "BAPC GYN ONCOLOGY",
        "BAPC OBSTETRICS AND GYNECOLOGY SUITE 400",
        "BAPC WOMENS WELLNESS CENTER AND SURVIVORSHIP",
        "DESC OBSTETRICS AND GYNECOLOGY",
        "OOMC OBSTETRICS AND GYNECOLOGY",
        "BAPC GYN ONCOLOGY ",
        "BNMC OBSTETRICS AND GYNECOLOGY",
        "OWCC OBSTETRICS AND GYNECOLOGY",
        "OWCC OBSTETRICS AND GYNECOLOGY",
        "ONLC OBSTETRICS AND GYNECOLOGY",
        "ZACC OBSTETRICS AND GYNECOLOGY",
        "WBMC OBSTETRICS AND GYNECOLOGY",
        "RACC OBSTETRICS AND GYNECOLOGY",
        "OLGC BRACC UROGYNECOLOGY",
        "NOMC GYN ONCOLOGY",
        "HGVC OBSTETRICS AND GYNECOLOGY",
    ]
    departments["PrimaryCare"] = [
        "ABSC FAMILY MEDICINE",
        "ALGC FAMILY MEDICINE",
        "BAPC INTERNAL MED",
        "BELC FAMILY MEDICINE/INTERNAL MED",
        "BFCC PRIMARY CARE",
        "BFGC PRIMARY CARE",
        "BLMC FAMILY MEDICINE/ INTERNAL MED",
        "BRBC PRIMARY CARE",
        "CENC INTERNAL MEDICINE",
        "DESC FAMILY HEALTH CENTER",
        "DHMC FAMILY MEDICINE",
        "DHSC FAMILY MEDICINE",
        "DSSC INTERNAL MEDICINE",
        "ELMC PRIMARY CARE",
        "GBSC PRIMARY CARE",
        "HGVC INTERNAL MEDICINE",
        "HGVC LIFESTYLE AND WELLNESS",
        "HMDC FAMILY MEDICINE",
        "HRDC Primary Care",
        "JPLC FAMILY MEDICINE",
        "KENC INTERNAL MEDICINE",
        "KNMC FAMILY MEDICINE",
        "KNMC INTERNAL MEDICINE",
        "KENC FAMILY MEDICINE",
        "LAPC FAMILY MED/ INTERNAL MED/ PEDS",
        "LMCC FAMILY MEDICINE",
        "LTRC PRIMARY CARE",
        "MATC FAMILY MEDICINE",
        "MECC FAMILY MEDICINE",
        "METC INTERNAL MEDICINE",
        "MIDC FAMILY MEDICINE",
        "NOMC CONCIERGE HEALTH - INTERNAL MEDICINE",
        "NOMC INTERNAL MEDICINE",
        "NSMC FAMILY MEDICINE",
        "NTCC PRIMARY CARE",
        "ONLC Internal Medicine",
        "OOMC PRIMARY CARE",
        "PRMC FAMILY PRACTICE",
        "PRVC INTERNAL MEDICINE",
        "SBPC OCHSNER PRIMARY CARE",
        "SCPC OCHSNER FAMILY MEDICINE",
        "SLIC FAMILY MEDICINE",
        "SMHC OCHSNER FAMILY MEDICINE",
        "SMHC OCHSNER PRIMARY CARE MEDVANTAGE",
        "SMOC FAMILY PRACTICE",
        "STAC INTERNAL MEDICINE",
        "BRBC PRIMARY CARE",
        "CENC INTERNAL MEDICINE",
        "DHMC FAMILY MEDICINE",
        "DSSC INTERNAL MEDICINE",
        "GBSC PRIMARY CARE",
        "HGVC INTERNAL MEDICINE",
        "HMDC FAMILY MEDICINE",
        "HRDC Primary Care",
        "JPLC FAMILY MEDICINE",
        "ONLC Internal Medicine",
        "PRVC INTERNAL MEDICINE",
        "ZACC INTERNAL MEDICINE",
        "OCVC PRIMARY CARE",
        "RETIRED ELMC PRIMARY CARE",
        "OLSC FA PRIMARY CARE",
        "LRSC PRIMARY CARE",
        "BFCC PRIMARY CARE",
        "SLIC VB PRIMARY CARE",
    ]
    departments["NLA"] = [
        "OLSC ACC INTERNAL MEDICINE",
        "OLSC FAM MED 4TH FLOOR",
        "OLSC PRV PRIMARY CARE",
        "OLSC PRV PRIMARY CARE/OLSC SV",
        "OLSC SV Primary Care",
        "OLSC FAM MED 5TH FLOOR",
        "SLPC PRIMARY CARE",
        "BMSC PRIMARY CARE",
    ]

    departments["NLAInclusive"] = departments["NLA"] + [
        "OLSC JW PRIMARY CARE",
    ]

    departments["OLG"] = ["LJFC FAMILY MEDICINE"]
    departments["BatonRouge"] = [
        "BRBC PRIMARY CARE",
        "CENC INTERNAL MEDICINE",
        "DHMC FAMILY MEDICINE",
        "DSSC INTERNAL MEDICINE",
        "GBSC PRIMARY CARE",
        "HGVC INTERNAL MEDICINE",
        "HGVC OBSTETRICS AND GYNECOLOGY",
        "HMDC FAMILY MEDICINE",
        "HRDC Primary Care",
        "JPLC FAMILY MEDICINE",
        "ONLC Internal Medicine",
        "ONLC OBSTETRICS AND GYNECOLOGY",
        "PRVC INTERNAL MEDICINE",
        "ZACC INTERNAL MEDICINE",
        "ZACC OBSTETRICS AND GYNECOLOGY",
    ]
    departments["BR_PrimaryCare"] = [
        "BRBC PRIMARY CARE",
        "CENC INTERNAL MEDICINE",
        "DHMC FAMILY MEDICINE",
        "DSSC INTERNAL MEDICINE",
        "GBSC PRIMARY CARE",
        "HGVC INTERNAL MEDICINE",
        "HMDC FAMILY MEDICINE",
        "HRDC Primary Care",
        "JPLC FAMILY MEDICINE",
        "ONLC Internal Medicine",
        "PRVC INTERNAL MEDICINE",
        "ZACC INTERNAL MEDICINE",
    ]
    departments["NLACardiology"] = [
        "OLSC DCI CARDIOLOGY",
        "OLMC CARDIOLOGY",
        "BMSC CARDIOLOGY",
    ]
    departments["Cardiology"] = [
        "BAPC CARDIOLOGY SUITE 230",
        "NOMC CARDIOLOGY",
        "METC CARDIOLOGY",
    ]

    departments["CardiologyInclusive"] = departments["Cardiology"] + [
        "PROV OMC CARDIOLOGY",
        "LAPC CARDIOLOGY",
        "OLMC CARDIOLOGY",
    ]

    departments["Urology"] = ["OLSC 255BK UROLOGY", "OLSC ACC UROLOGY"]
    departments["UrologyInclusive"] = departments["Urology"] + [
        "OLSC 255BK UROLOGY PROCEDURES",
    ]
    longDepList = (
        departments["OBGYN"]
        + departments["NLA"]
        + departments["OLG"]
        + departments["Urology"]
    )
    departments["OBGYN_2"] = []
    obgyn = {
        x
        for x in departments_source
        if any(ele in x.lower() for ele in {"obst", "gyn", "women"})
    }

    obgyn.update(departments["OBGYN"])
    departments["OBGYN_2"] = obgyn
    all_departments = {x for x in departments_source}
    longDeptList = (
        list(departments["OBGYN_2"])
        + list(departments["NLA"])
        + departments["OLG"]
        + departments["Urology"]
        + departments["Cardiology"]
    )
    departments["Urology"] = [
        x for x in longDepList if re.search(r"\burology\b", x, re.I)
    ]
    sarah = {x for x in departments_source if x not in longDeptList}
    counted_departments = [
        x
        for y in ["OBGYN_2", "NLA", "Urology", "PrimaryCare", "Cardiology"]
        for x in departments[y]
    ]
    extra_departments = [x for x in sarah if x not in departments["PrimaryCare"]]
    departments["PrimaryCare"] = sarah
    departments["TOTAL"] = all_departments
    departments["Extras"] = extra_departments
    departments["ReExtras"] = sorted(set(all_departments) - set(counted_departments))
    # extras_to_csv(extra_departments)
    # extras_to_csv(departments["ReExtras"])
    return departments


def extras_to_csv(extras: list[str], month=None):
    now = dt.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"serviceline_output/extra_departments_{now}.csv"
    with open(filename, "w", newline="") as file:
        csvwriter = writer(file)
        csvwriter.writerow(["Extra Departments", "toCopy", "Month"])
        csvwriter.writerows([[x, f"'{x}',", month] for x in extras])
    print(Path(filename).absolute())


def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        print(f"func:{f.__name__} args:[{args}, {kwargs}] took: {te - ts:.2f} sec")
        return result

    return wrap
