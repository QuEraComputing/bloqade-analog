# Migrating to Bloqade Analog

## Introduction

In order to make room for more features inside the Bloqade ecosystem, we have created a new package to take the place of the old `bloqade` package. The new package is called `bloqade-analog`. The old package `bloqade` will house a namespace package for other features such as our new Bloqade Digital package with support for circuit-based quantum computers!

## Installation

You can install the package with `pip` in your Python environment of choice via:

```sh
pip install bloqade-analog
```

## Migration

The new package is a drop-in replacement for the old one. You can simply replace `import bloqade` with `import bloqade.analog`  or `from bloqade.analog import ...` in your code. Everything else should work as before.

## Example

lets say your header of your python script looks like this:

```python
from bloqade import var
from bloqade.atom_arrangement import Square
...
```
You can simply replace it with:

```python
from bloqade.analog import var
from bloqade.analog.atom_arrangement import Square
...
```

## Migrating old bloqade JSON files

If you have old bloqade JSON files, you will not be able to directly deserialize them anymore because of the package restructuring. However, we have provided some tools to migrate those JSON files to be compatible with `bloqade-analog`. You can do this by running the following command in the command line for a one or more files:

```sh
python -m bloqade.analog.migrate <path_to_old_json_file1> <path_to_old_json_file2> ...
```
With default arguments this will create a new file with the same name as the old file, but with `-analog` appended to the end of the filename. For example, if you have a file called `my_bloqade.json`, the new file will be called `my_bloqade-analog.json`. You can then use `load` to deserialize this file with the `bloqade-analog` package. There are other options for converting the file, such as setting the indent level for the output file or overwriting the old file. You can see all the options by running:

```sh
python -m bloqade.analog.migrate --help
```

Another option is to use the migration tool in a python script:

```python
from bloqade.analog.migrate import migrate

 # set the indent level for the output file
indent: int = ...
# set to True if you want to overwrite the old file, otherwise the new file will be created with -analog appended to the end of the filename
overwrite: bool = ...
f
or filename in ["file1.json", "file2.json", ...]:
    migrate(filename, indent=indent, overwrite=overwrite)
```
This will migrate all the files in the list to the new format.


## Having trouble, comments, or concerns?

Please open an issue on our [GitHub](https://github.com/QuEraComputing/bloqade-analog/issues)
