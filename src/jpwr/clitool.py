import argparse
import os
import re
import subprocess
import time
import traceback
import unicodedata

import pandas as pd

from .ctxmgr import get_power

def get_pynvml_method():
    from jpwr.gpu.pynvml import power
    return power()

def get_rocm_method():
    from jpwr.gpu.rocm import power
    return power()

def get_gh_method():
    from jpwr.sys.gh import power
    return power()

def save_df_hdf5(df : pd.DataFrame, filename : str):
    df.to_hdf(path_or_buf=filename, key="jpwr", mode='w', complib="blosc:zstd")

def save_df_csv(df : pd.DataFrame, filename : str):
    df.to_csv(path_or_buf=filename)


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


methods = {
    "pynvml": get_pynvml_method,
    "rocm": get_rocm_method,
    "gh": get_gh_method,
}

df_filesavers = {
    "h5": save_df_hdf5,
    "csv": save_df_csv
}

def parse_args():

    default_interval = 100 #ms
    parser = argparse.ArgumentParser(description="jpwr - JSC power measurement tool")
    parser.add_argument("--methods",
        type=str,
        nargs="+",
        required=True,
        choices=methods.keys(),
        help=f"Choose method by which to measure power. Choices: [{','.join(methods.keys())}]")
    parser.add_argument("--interval",
        type=int,
        default=default_interval,
        help=f"interval between measurement in ms (default: {default_interval})")
    parser.add_argument("--df-out",
        type=str,
        help=f"Directory to write dataframes with acquired power measurements to")
    parser.add_argument("--df-filetype",
        type=str,
        choices=df_filesavers.keys(),
        default=list(df_filesavers.keys())[0],
        help=f"File type to use for dataframes. Choices: [{','.join(df_filesavers.keys())}]")
    parser.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command to run with the tool",
    )

    return parser.parse_args()

def main():

    args = parse_args()
    if args.cmd is None:
        print("no command specified")
        exit(-1)

    if args.cmd[0] == '--':
        args.cmd = args.cmd[1:]
    
    power_methods = [methods[m]() for m in set(args.methods)]

    print(f"Measuring Energy while executing {args.cmd}")
    with get_power(power_methods, args.interval) as measured_scope:
        try:
            result = subprocess.run(args.cmd, text=True)
        except Exception as exc:
            import traceback
            print(f"Errors occured during power measurement of '{args.cmd}': {exc}")
            print(f"Traceback: {traceback.format_exc()}")
    power=measured_scope.df
    energy,additional = measured_scope.energy()
    print("Power data:")
    print(power)
    print("Energy data:")
    print(energy)
    if(additional.items()):
        print("Additional data:")
    for k,v in additional.items():
        print(f"{k}:")
        print(v)

    if (args.df_out):
        if not os.path.exists(args.df_out):
            os.makedirs(args.df_out)
        if not os.path.isdir(args.df_out):
            raise ValueError(f"{args.df_out} is not a directory")

        import platform
        suffix = f"{platform.node()}.{os.getpid()}"

        save_df = df_filesavers[args.df_filetype]
        print(f"Writing measurements to {args.df_out}")
        power_path = os.path.join(args.df_out, f"power.{suffix}.{args.df_filetype}")
        print(f"Writing power df to {power_path}")
        save_df(power, power_path)
        energy_path = os.path.join(args.df_out, f"energy.{suffix}.{args.df_filetype}")
        print(f"Writing energy df to {energy_path}")
        save_df(energy, energy_path)
        for k,v in additional.items():
            additional_path = os.path.join(args.df_out, f"{slugify(k)}.{suffix}.{args.df_filetype}")
            print(f"Writing {k} df to {additional_path}")
            save_df(v, additional_path)

        
