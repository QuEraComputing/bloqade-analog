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

## Having trouble, comments, or concerns?

Please open an issue on our [GitHub](https://github.com/QuEraComputing/bloqade-analog/issues)
