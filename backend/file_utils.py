import pathlib
from pathlib import Path
from sys import argv
from tkinter import filedialog as fd
import datetime as dt
import msoffcrypto
import pandas as pd


# args_n = len(argv)
# use_args = False
# print(argv)
# if args_n == 3:
#     use_args = True
#     arg_filepath = rf"{argv[1]}"
#     arg_sheetname = argv[2]


def filedialog() -> str:
    folder = path.split("\\")
    folder.remove(folder[-1])
    folder = "\\".join(folder)
    newpath = fd.askopenfile(initialdir=folder, typevariable=str).name
    return newpath


def decrypt_xlsx(filepath, password="orc123"):
    decrypted_wb = io.BytesIO()
    with open(filepath, "rb") as file:
        office_file = msoffcrypto.OfficeFile(file)
        office_file.load_key(password=password)
        office_file.decrypt(decrypted_wb)
    df = pd.read_excel(decrypted_wb)
    return df


def pckl_path() -> str:
    pickle_path = path.split(".")
    del pickle_path[-1]
    pickle_path = "".join(pickle_path) + sheet + ".pckl"
    return pickle_path

def select_file():
    args_n = len(argv)
    use_args = False
    print(argv)
    if args_n == 3:
        use_args = True
        arg_filepath = rf"{argv[1]}"
        arg_sheetname = argv[2]
    if use_args:
        path = arg_filepath
        sheet = arg_sheetname
    else:
        path = filedialog()
        if path[-4:] != ".csv":
            sheetnames = pd.ExcelFile(path).sheet_names
            print([f"{i}. {x}" for i, x in enumerate(sheetnames)])
            sheet = sheetnames[int(input("Which sheet would you like to use? "))]
    pickled = Path(pckl_path()).exists()
    if pickled:
        print("Using pickle")
        df = pd.read_pickle(pckl_path())
    else:
        if path[-4:] == ".csv":
            print("Reading CSV")
            df = pd.read_csv(path, index_col=False, header=0, engine="python")
            sheet = dt.datetime.now().strftime("%b")

        elif path[-5:] == ".pckl":
            print("Reading pickle.")
            df = pd.read_pickle(path)
        else:
            print("Reading XLSX")
            if "flat" in path:
                df = pd.read_excel(path)
            else:
                try:
                    df = pd.read_excel(path, sheet_name=sheet)
                except:
                    df = decrypt_xlsx(path)
        df.replace(np.nan, "", inplace=True)
        df.to_pickle(pckl_path())
    print(df.columns)
    return df
