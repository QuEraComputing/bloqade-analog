from typing import IO, Any, Dict, List
from dataclasses import field, dataclass

import simplejson as json


@dataclass
class JSONWalker:
    has_done_something: bool = field(init=False, default=False)

    def walk_dict(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        new_obj = {}
        for key, value in obj.items():

            if key.startswith("bloqade.analog."):
                new_obj[key] = self.walk(value)
            elif key.startswith("bloqade."):
                new_obj[key.replace("bloqade.", "bloqade.analog.")] = self.walk(value)
                self.has_done_something = True
            else:
                new_obj[key] = self.walk(value)

        return new_obj

    def walk(self, obj: Dict[str, Any] | List[Any]) -> Dict[str, Any] | List[Any]:
        if isinstance(obj, dict):
            return self.walk_dict(obj)
        elif isinstance(obj, list):
            return list(map(self.walk, obj))
        else:
            return obj

    def convert(self, obj: Dict[str, Any] | List[Any]):
        self.has_done_something = False
        new_obj = self.walk(obj)
        return new_obj, self.has_done_something


def _migrate(input_oi: IO[str], output_oi: IO[str], indent: int | None = None):
    obj = json.load(input_oi)
    new_obj, has_done_something = JSONWalker().convert(obj)

    if has_done_something:
        json.dump(new_obj, output_oi, indent=indent)


def migrate(
    filename: str,
    indent: int | None = None,
    overwrite: bool = False,
):
    new_filename = filename if overwrite else filename.replace(".json", "-analog.json")
    with open(filename, "r") as in_io, open(new_filename, "w") as out_io:
        _migrate(in_io, out_io, indent)


def _entry():
    import argparse

    import tqdm

    parser = argparse.ArgumentParser()

    parser.add_argument("filenames", type=str, nargs="*")
    parser.add_argument("--indent", type=int, default=None)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the original file",
        default=False,
    )

    args = parser.parse_args()
    for filename in tqdm.tqdm(args.filenames):
        migrate(filename, args.indent, args.overwrite)


if __name__ == "__main__":
    _entry()
