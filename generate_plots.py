""""
Generate LUX/OD600 and OD600 plots from data provided in .xlsx files created by TECAN microplate reader.

Usage:
    Basic mod:
        ======================== Basic Utility =========================
            python geberate_plots.py

            Generates LUX/OD600 plots from all viable files in the scripts directory.

    Advanced settings:
        ======================== Multiple Files ========================
            python generate_plots.py --input /path/to/input --out /path/to/output --variant {OD600 or LuxByOd}

            This setup genrates plots from all viable files in input directory and outputs them in the output directory.
            The variant flag determins whether the plots will be of LUX/OD600 or just OD600 (defaults to LUX/OD600)


        ======================== Single File ===========================
            python generate_plots.py --file-name {file_name} --out /path/to/output --variant {OD600 or LuxByOd}

            This will work with just one file of given name (it must be stored next to the python file).
            Other options as described above.

Output Structure:
    ======================== Default Output Directory =========================
        /python/file/directory/out_{current time}/
            ├── LuxByOd
            │   └── {file}_LuxByOD
            │       ├── {file}_LuxByOD_1.png
            │       ├── {file}_LuxByOD_2.png
            │       ├── {file}_LuxByOD_3.png
            │       └── {file}_LuxByOD_4.png
            └── OD600
                └── {file}_OD600
                    ├── {file}_OD600_1.png
                    ├── {file}_OD600_2.png
                    ├── {file}_OD600_3.png
                    └── {file}_OD600_4.png



    ======================== Custom Output Directory =========================
        /custom/output/directory/
            ├── LuxByOd
            │   └── {file}_LuxByOD
            │       ├── {file}_LuxByOD_1.png
            │       ├── {file}_LuxByOD_2.png
            │       ├── {file}_LuxByOD_3.png
            │       └── {file}_LuxByOD_4.png
            └── OD600
                └── {file}_OD600
                    ├── {file}_OD600_1.png
                    ├── {file}_OD600_2.png
                    ├── {file}_OD600_3.png
                    └── {file}_OD600_4.png

                    
    ####### If you run the script with just one variant (OD600 or LUX/OD600), only one subfolder will be created #######
    
"""
import pandas as pd
import numpy as np
import pathlib
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from datetime import datetime
import sys

# ========================= Base Background Values =========================
OD600_MEAN = 0.095275
OD600_STD_DEV = 0.001085

LUX_MEAN = 64.0
LUX_STD_DEV = 12.351981



# ========================= Function Declarations =========================
def xlsx_to_dataframe(xlsx_path: pathlib.Path) -> pd.DataFrame:
    """
    Reads an excel .xlsx file into pandas.Dataframe, extracts OD600 and LUX data, calculates lux/od and returns,
    its mean values and standard deviations as pandas.Dataframes.
    """
    df = pd.read_excel(xlsx_path).iloc[:, :12]

    # Extracting parts of the file with our information
    od = df[45:141:1].reset_index(drop=True)
    lux = df[146:242:1].reset_index(drop=True)

    cols = od.columns

    # Checking for incorrect datatypes
    for col in cols[1:]:
        od[col] = pd.to_numeric(od[col], errors="coerce")
        lux[col] = pd.to_numeric(lux[col], errors="coerce")

    numeric_cols = od.select_dtypes(include="number").columns

    od[numeric_cols] -= OD600_MEAN * np.ones_like(od[numeric_cols])
    lux[numeric_cols] -= LUX_MEAN * np.ones_like(lux[numeric_cols])

    lux_by_od = od.copy()

    # Calculating LUX/OD600
    lux_by_od[numeric_cols] = lux[numeric_cols].div(od[numeric_cols], fill_value=1)

    # Means and standard deviations
    lux_by_od_median = lux_by_od.select_dtypes(include="number").groupby(np.arange(len(lux_by_od)) // 3).mean()
    std_devs = lux_by_od_median.groupby(np.arange(len(lux_by_od_median)) // 4).std()
    means = lux_by_od_median.groupby(np.arange(len(lux_by_od_median)) // 4).mean()

    return means, std_devs


def xlsx_to_dataframe_od(xlsx_path: pathlib.Path) -> pd.DataFrame:
    """
    Reads OD600 data from .xlsx file into a pandas.Dataframe. Returns means and standard deviations for different samples.
    """
    df = pd.read_excel(xlsx_path).iloc[:, :12]


    od = df[45:141:1].reset_index(drop=True)

    cols = od.columns

    for col in cols[1:]:
        od[col] = pd.to_numeric(od[col], errors="coerce")

    numeric_cols = od.select_dtypes(include="number").columns

    od[numeric_cols] -= OD600_MEAN * np.ones_like(od[numeric_cols])


    od_means = od.select_dtypes(include="number").groupby(np.arange(len(od)) // 3).mean()
    std_devs = od_means.groupby(np.arange(len(od_means)) // 4).std()
    means = od_means.groupby(np.arange(len(od_means)) // 4).mean()

    return means, std_devs



def make_plots(means: pd.DataFrame, std_devs: pd.DataFrame, file_name: str, out_path: pathlib.Path, no=4):
    """
    Creates line plots with confidence intervals with data from means and std_devs.
    """
    letters = "ABCDEFGH"
    out_path.mkdir(parents=True, exist_ok=True)

    if file_name[-5:] == "OD600":
        title = "OD600"
    else:
        title = "LUX/OD600"

    for k in range(no):
        n = 2*k

        a_mean = means.iloc[n]
        b_mean = means.iloc[n+1]

        a_dev = std_devs.iloc[n]
        b_dev = std_devs.iloc[n+1]

        time = np.arange(0, 301, 30)

        df_A = pd.DataFrame({
            'Time': time,
            'Mean': a_mean,
            'Upper': a_mean + a_dev,
            'Lower': a_mean - a_dev
        })

        df_B = pd.DataFrame({
            'Time': time,
            'Mean': b_mean,
            'Upper': b_mean + b_dev,
            'Lower': b_mean - b_dev
        })


        sns.set_theme(style="whitegrid", palette="muted")
        plt.figure(figsize=(12, 6))

        # Plotting sample A
        sns.lineplot(data=df_A, x="Time", y="Mean", color="blue", label=f"{letters[n]}")
        plt.fill_between(df_A["Time"], df_A["Lower"], df_A["Upper"], alpha=0.2, color="#1800a0")

        # Plotting sample B
        sns.lineplot(data=df_B, x="Time", y="Mean", color="red", label=f"{letters[n+1]}")
        plt.fill_between(df_B["Time"], df_B["Lower"], df_B["Upper"], alpha=0.2, color="#a00000")

        # Cosmetics
        plt.xlim(0, 300)
        plt.xticks(np.arange(0, 301, 30))
        plt.grid(axis='x', linestyle='--', alpha=1)
        plt.title(f"Plot {title} samples {letters[n]} and {letters[n+1]}")
        plt.xlabel("Time (min)")
        plt.ylabel(title)
        plt.legend(loc="upper left")


        plt.savefig(out_path/(file_name+f"_{np.floor(n/2).astype(int)+1}.png"))
        plt.close()



def main():
    p = argparse.ArgumentParser(description="Generate time series plots from scanner data in .xlsx format.")
    p.add_argument("--input", type=pathlib.Path, default=None)
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path(__file__).parent.resolve()/("out_"+datetime.now().strftime("%Y%m%d_%H%M")))
    p.add_argument("--variant", type=str, default=None)
    p.add_argument("--file-name", type=str)
    args = p.parse_args()

    if (not args.file_name) and (not args.input):
        args.input = pathlib.Path(__file__).parent.resolve()

    if args.file_name and args.input:
        print("You can choose only one out of the two: input directory OR file name.")
        sys.exit(1)

    if args.file_name:
        file_path = pathlib.Path(__file__).parent.resolve()/args.file_name

        if args.variant == "OD600":
            means, std_devs = xlsx_to_dataframe_od(file_path)
        else:
            means, std_devs = xlsx_to_dataframe(file_path)    

        make_plots(means, std_devs, args.file_name, pathlib.Path(__file__).parent.resolve()/(args.file_name[:-5]))
    else:
        if args.variant == "OD600":
            xlsx_files = args.input.rglob("*.xlsx")

            if not xlsx_files:
                print("No .xlsx files found in your directory and no cutom directory was provided.")
                sys.exit(1)

            args.out.mkdir(exist_ok=True, parents=True)

            for file in xlsx_files:
                try:
                    means, std_devs = xlsx_to_dataframe_od(file)
                    make_plots(means, std_devs, file.stem+"_OD600", args.out/"OD600"/(file.stem+"_OD600"))
                except Exception as e:
                    print(f"Couldnt process file {file} with exception {e}")

        elif args.variant == "LuxByOd":
            xlsx_files = list(args.input.rglob("*.xlsx"))


            if len(xlsx_files) == 0:
                print("No .xlsx files found in your directory and no cutom directory was provided.")
                sys.exit(1)

            args.out.mkdir(exist_ok=True, parents=True)

            for file in xlsx_files:
                try:
                    means, std_devs = xlsx_to_dataframe(file)
                    make_plots(means, std_devs, file.stem+"_LuxByOd", args.out/"LuxByOd"/(file.stem+"_LuxByOD"))
                except Exception as e:
                    print(f"Couldnt process file {file} with exception {e}")
        else:
            xlsx_files = list(args.input.rglob("*.xlsx"))

            if len(xlsx_files) == 0:
                print("No .xlsx files found in your directory and no cutom directory was provided.")
                sys.exit(1)

            args.out.mkdir(exist_ok=True, parents=True)


            for file in xlsx_files:
                try:
                    means, std_devs = xlsx_to_dataframe(file)
                    make_plots(means, std_devs, file.stem+"_LuxByOd", args.out/"LuxByOd"/(file.stem+"_LuxByOD"))

                    means_od, std_devs_od = xlsx_to_dataframe_od(file)
                    make_plots(means_od, std_devs_od, file.stem+"_OD600", args.out/"OD600"/(file.stem+"_OD600"))
                except Exception as e:
                    print(f"Couldnt process file {file} with exception {e}")



if __name__ == "__main__":
    main()
