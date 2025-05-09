# JSC power tool

JPWR is a modular tool for measuring power and energy of different compute devices. Right now the tool supports methods for querying AMD GPUs, NVIDIA GPUs, specific methods for getting system power on NVIDIA Grace-Hopper nodes and the GraphCore GC200 IPU.

Basic functionality is provided by starting a power-measurement loop in a separate thread that uses device-specific interfaces to query device power periodically, saving the datapoints along with timestamps internally and calculating the energy consumed at the end of operation.

The device-specific interfaces are called "methods" and are implemented in:

| Backend            | Method name | Source code                                      |
| ------------------ | ----------- | ------------------------------------------------ |
| ROCM smi           | rocm        | [src/jpwr/gpu/rocm.py](src/jpwr/gpu/rocm.py)     |
| PyNVML             | pynvml      | [src/jpwr/gpu/pynvml.py](src/jpwr/gpu/pynvml.py) |
| Grace-Hopper sysfs | gh          | [src/jpwr/sys/gh.py](src/jpwr/sys/gh.py)         |
| GraphCore IPU info | gc          | [src/jpwr/ipu/gc.py](src/jpwr/ipu/gc.py)         |

The user can choose to use either the command-line tool `jpwr` or use the `get_power` context manager from [src/jpwr/ctxmgr.py](src/jpwr/ctxmgr.py) programmatically on ROIs withing a python program.

For `jpwr` usage examples, see [CLI tool usage examples](#cli-tool-usage-examples).

For programmatic usage, please refer to either the [cli tool source](src/jpwr/clitool.py) or the [tests](test).

## Quickstart

```
$ pipx install git+https://github.com/FZJ-JSC/jpwr
$ jpwr -h
usage: clitool.py [-h] --methods {pynvml,rocm,gh} [{pynvml,rocm,gh} ...] [--interval INTERVAL] [--use-mpi] [--mpi-ranks rank [rank ...]] [--df-suffix DF_SUFFIX] [--df-out DF_OUT] [--df-filetype {h5,csv}] ...

jpwr - JSC power measurement tool
[...]
```

## Build and install with all optional dependencies
```
cd jpwr
python -m build
pip install dist/jwpr-0.0.10-py3-none-any.whl\[pynvml,mpi\]
```

## CLI tool usage examples
ROCM-supported GPU:
```
ᐅ jpwr --methods rocm --df-out energy_meas --df-filetype csv stress-ng --gpu 8 -t 5
Measuring Energy while executing ['stress-ng', '--gpu', '8', '-t', '5']
stress-ng: info:  [79366] setting to a 5 secs run per stressor
stress-ng: info:  [79366] dispatching hogs: 8 gpu
stress-ng: info:  [79375] gpu: GL_VENDOR: AMD
stress-ng: info:  [79375] gpu: GL_VERSION: OpenGL ES 3.2 Mesa 24.1.3-arch1.2
stress-ng: info:  [79375] gpu: GL_RENDERER: AMD Radeon RX 6800 XT (radeonsi, navi21, LLVM 18.1.8, DRM 3.57, 6.9.6-273-tkg-bore)
stress-ng: info:  [79366] skipped: 0
stress-ng: info:  [79366] passed: 8: gpu (8)
stress-ng: info:  [79366] failed: 0
stress-ng: info:  [79366] metrics untrustworthy: 0
stress-ng: info:  [79366] successful run completed in 5.03 secs
Power data:
       timestamps  rocm:0
0    1.720624e+09    17.0
1    1.720624e+09    20.0
2    1.720624e+09    20.0
3    1.720624e+09    33.0
4    1.720624e+09    33.0
..            ...     ...
96   1.720624e+09    45.0
97   1.720624e+09    46.0
98   1.720624e+09    46.0
99   1.720624e+09    46.0
100  1.720624e+09    46.0

[101 rows x 2 columns]
Energy data:
rocm:0    0.061672
dtype: float64
Additional data:
energy_from_counter:
   rocm:0
0     0.0
Writing measurements to energy_meas
Writing power df to energy_meas/power.csv
Writing energy df to energy_meas/energy.csv
Writing energy_from_counter df to energy_meas/energy_from_counter.csv
```
Grace-Hopper node:
```
ᐅ jpwr --methods pynvml gh --df-out energy_meas/ --interval 1000 stress-ng --cpu 24 -t 10
Measuring Energy while executing ['stress-ng', '--cpu', '24', '-t', '10']
stress-ng: info:  [24331] setting to a 10 secs run per stressor
stress-ng: info:  [24331] dispatching hogs: 24 cpu
stress-ng: info:  [24331] skipped: 0
stress-ng: info:  [24331] passed: 24: cpu (24)
stress-ng: info:  [24331] failed: 0
stress-ng: info:  [24331] metrics untrustworthy: 0
stress-ng: info:  [24331] successful run completed in 10.05 secs
Power data:
      timestamps  pynvml:0  pynvml:1  pynvml:2  pynvml:3  gh:Module Power Socket 0  ...  gh:CPU Power Socket 2  gh:SysIO Power Socket 2  gh:Module Power Socket 3  gh:Grace Power Socket 3  gh:CPU Power Socket 3  gh:SysIO Power Socket 3
0   1.720686e+09   108.244    91.588    94.856   105.360                   165.627  ...                 30.399                    0.107                   197.148                   36.714                 35.134                    0.171
1   1.720686e+09   112.458    91.686    94.718   105.270                   165.627  ...                 30.399                    0.107                   197.148                   36.714                 35.134                    0.171
2   1.720686e+09   112.458    91.686    94.718   105.270                   216.054  ...                 30.399                    0.120                   192.957                   36.943                 35.658                    0.171
3   1.720686e+09   112.989    91.499    94.738   105.249                   216.054  ...                 30.399                    0.120                   192.957                   36.943                 35.658                    0.171
4   1.720686e+09   112.989    91.499    94.738   105.249                   218.098  ...                 29.886                    0.113                   199.244                   36.447                 35.134                    0.167
5   1.720686e+09   113.129    91.598    94.797   105.270                   218.098  ...                 29.886                    0.113                   199.244                   36.447                 35.134                    0.167
6   1.720686e+09   113.142    91.598    94.793   105.242                   218.088  ...                 30.409                    0.107                   193.001                   36.425                 35.123                    0.171
7   1.720686e+09   113.000    91.459    94.868   105.263                   218.088  ...                 30.409                    0.107                   193.001                   36.425                 35.123                    0.171
8   1.720686e+09   113.000    91.459    94.868   105.263                   218.108  ...                 30.410                    0.105                   197.148                   36.954                 35.636                    0.171
9   1.720686e+09   113.057    91.315    94.845   105.341                   218.108  ...                 30.410                    0.105                   197.148                   36.954                 35.636                    0.171
10  1.720686e+09   113.057    91.298    94.845   105.341                   216.003  ...                 29.886                    0.118                   197.148                   35.854                 34.589                    0.150
11  1.720686e+09   113.097    91.353    94.711   105.304                   216.003  ...                 29.886                    0.118                   197.148                   35.854                 34.589                    0.150
12  1.720686e+09   113.055    91.353    94.711   105.285                   218.139  ...                 30.933                    0.113                   195.008                   36.419                 35.134                    0.154
13  1.720686e+09   113.029    91.377    94.867   105.356                   218.139  ...                 30.933                    0.113                   195.008                   36.419                 35.134                    0.154
14  1.720686e+09   113.029    91.377    94.814   105.356                   218.098  ...                 29.886                    0.111                   197.106                   36.452                 35.134                    0.171
15  1.720686e+09   113.012    91.500    94.681   105.238                   218.098  ...                 29.886                    0.111                   197.106                   36.452                 35.134                    0.171
16  1.720686e+09   113.012    91.515    94.681   105.238                   218.065  ...                 30.410                    0.111                   197.106                   37.467                 36.182                    0.171
17  1.720686e+09   112.914    91.355    94.829   105.287                   218.065  ...                 30.410                    0.111                   197.106                   37.467                 36.182                    0.171
18  1.720686e+09   112.936    91.355    94.829   105.286                   218.099  ...                 29.886                    0.101                   197.102                   36.427                 35.134                    0.163

[19 rows x 21 columns]
Energy data:
pynvml:0                    0.283475
pynvml:1                    0.229511
pynvml:2                    0.237850
pynvml:3                    0.264206
gh:Module Power Socket 0    0.531902
gh:Grace Power Socket 0     0.259043
gh:CPU Power Socket 0       0.251467
gh:SysIO Power Socket 0     0.002747
gh:Module Power Socket 1    0.432144
gh:Grace Power Socket 1     0.084860
gh:CPU Power Socket 1       0.081138
gh:SysIO Power Socket 1     0.000647
gh:Module Power Socket 2    0.460729
gh:Grace Power Socket 2     0.078853
gh:CPU Power Socket 2       0.076006
gh:SysIO Power Socket 2     0.000280
gh:Module Power Socket 3    0.492371
gh:Grace Power Socket 3     0.091918
gh:CPU Power Socket 3       0.088587
gh:SysIO Power Socket 3     0.000417
dtype: float64
Writing measurements to energy_meas/
Writing power df to energy_meas/power.jpbot-001-17.jupiter.internal.24321.h5
Writing energy df to energy_meas/energy.jpbot-001-17.jupiter.internal.24321.h5
```

## MPI support

> :warning: `--use-mpi` will initialize MPI inside of the jpwr tool, which very likely will lead to errors when the profiled application tries to initialize MPI itself. For now please use `--df-suffix` in conjunction with environment variables using the `%q{}` syntax to generate unique filenames.

use `--use-mpi` to add the mpi rank as suffix to the filename:

```
ᐅ mpirun -n 2 jpwr --methods pynvml --df-out energy_meas --use-mpi -- stress-ng --gpu 2
Measuring Energy while executing ['stress-ng', '--gpu', '2']
Measuring Energy while executing ['stress-ng', '--gpu', '2']
[...]
Writing measurements to energy_meas
Writing power df to energy_meas/power.1.h5
Writing measurements to energy_meas
Writing power df to energy_meas/power.0.h5
Writing energy df to energy_meas/energy.1.h5
Writing energy df to energy_meas/energy.0.h5
```

use `--mpi-ranks` to restrict energy measurement to specified mpi ranks:

```
ᐅ mpirun -n 2 jpwr --methods pynvml --df-out energy_meas --use-mpi --mpi-ranks 0 -- stress-ng --gpu 2
Executing ['stress-ng', '--gpu', '2']
Measuring Energy while executing ['stress-ng', '--gpu', '2']
[...]
Writing measurements to energy_meas
Writing power df to energy_meas/power.0.h5
Writing energy df to energy_meas/energy.0.h5
```

## Ignore measurement errors

There appears to be an issue with pynvml sometimes erroring out when measuring device power, the `--ignore-measure-errors` option was added to the tool to skip a measurement if any of the power methods error out/return an exception. Without that flag, the measuring process will crash if an error occurs.
