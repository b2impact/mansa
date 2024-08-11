import argparse  # noqa: D100
import ast
import json
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Union

import toml
from rich import print

VALID_TAGS = {
    "environment": ["sbx", "dev", "pre", "pro", "hub"],
    "businessOwner": re.compile(r".+@.+\..+"),
    "technicalOwner": re.compile(r"[A-Za-z]{1,4}-[A-Za-z]+"),
    "businesUnit": re.compile(r"^[A-Za-z]{3}$"),
    "source": ["terraform", "portal", "amlsdkv2", "amlsdkv1"],
    "ismsClassification": ["l", "m", "m"],
}


class MansaLinter(ast.NodeVisitor):
    """
    MansaLinter _summary_.

    Parameters
    ----------
    ast : _type_
        _description_
    """

    def __init__(self, config):
        self.errors = []
        self.target_classes = self.find_target_classes(config)

    def find_target_classes(self, config: dict, path: Union[list, None] = None) -> Union[dict, None]:
        """
        Detect automatically the configuration of a toml file.

        Parameters
        ----------
        config : _type_
            _description_
        path : _type_, optional
            _description_, by default None

        Returns
        -------
        Any | dict
            _description_
        """
        if path is None:
            path = []

        if isinstance(config, dict):
            for key, value in config.items():
                new_path = path + [key]
                if key == "target_classes":
                    return value
                result = self.find_target_classes(value, new_path)
                if result:
                    return result
        return None

    def visit_Call(self, node) -> None:  # noqa: N802 # Abstract Syntax Tree (AST) and NodeVisitor
        """
        Overwrite ast.NodeVisitor.visit_Call().

        Parameters
        ----------
        node : _type_
            _description_
        """
        if isinstance(node.func, ast.Name) and node.func.id in self.target_classes:
            tags_arg = next((keyword for keyword in node.keywords if keyword.arg == "tags"), None)
            if not tags_arg:
                error_code = self.target_classes[node.func.id]
                self.errors.append(
                    (
                        node.lineno,
                        node.func.id,
                        f"""{error_code}: '{node.func.id}' instantiation is missing 'tags' argument""",
                    )
                )
            else:
                self.validate_tags(node.lineno, node.func.id, tags_arg.value)
        self.generic_visit(node)

    def validate_tags(self, lineno, class_name, tags_node) -> None:
        """
        validate_tags _summary_.

        Parameters
        ----------
        lineno : _type_
            _description_
        class_name : _type_
            _description_
        tags_node : _type_
            _description_
        """
        if not isinstance(tags_node, ast.Dict):
            self.errors.append((lineno, class_name, "Tags argument is not a valid dictionary"))
            return
        for key, value in zip(tags_node.keys, tags_node.values):  # noqa: B905
            key_str = key.s if isinstance(key, ast.Constant) else None
            value_str = value.s if isinstance(value, ast.Constant) else None

            if key_str not in VALID_TAGS:
                self.errors.append((lineno, class_name, f"Invalid tag key '{key_str}'"))
                continue

            valid_values = VALID_TAGS[key_str]
            if isinstance(valid_values, list) and value_str not in valid_values:
                self.errors.append((lineno, class_name, f"Invalid value '{value_str}' for key '{key_str}'"))
            elif isinstance(valid_values, re.Pattern) and not valid_values.match(value_str):
                self.errors.append((lineno, class_name, f"Invalid format for value '{value_str}' for key '{key_str}'"))


def lint_code(code: str, config: dict) -> list:
    """
    lint_code _summary_.

    Parameters
    ----------
    code : str
        _description_
    config : dict
        _description_

    Returns
    -------
    list
        _description_
    """
    tree = ast.parse(code)
    linter = MansaLinter(config)
    linter.visit(tree)
    return linter.errors


def lint_notebook(nb_path: str, config: dict) -> list:
    """
    lint_notebook _summary_.

    Parameters
    ----------
    nb_path : str
        _description_
    config : dict
        _description_

    Returns
    -------
    list
        _description_
    """
    with open(nb_path, "r") as f:
        notebook = json.load(f)
    errors = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            code = "".join(cell["source"])
            errors.extend(lint_code(code, config))
    return errors


def scan_directory(directory: str) -> tuple[list, list]:
    """
    scan_directory _summary_.

    Parameters
    ----------
    directory : str
        _description_

    Returns
    -------
    tuple[list, list]
        _description_
    """
    py_files = []
    ipynb_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
            elif file.endswith(".ipynb"):
                ipynb_files.append(os.path.join(root, file))
    return py_files, ipynb_files


def process_file(filepath: str, config: dict) -> list[tuple]:
    """
    process_file _summary_.

    Parameters
    ----------
    filepath : str
        _description_
    config : dict
        _description_

    Returns
    -------
    list[tuple]
        _description_
    """
    if filepath.endswith(".py"):
        with open(filepath, "r") as file:
            code = file.read()
        lint_errors = lint_code(code, config)
        errors = [(filepath, lineno, name, message) for lineno, name, message in lint_errors]
    elif filepath.endswith(".ipynb"):
        lint_errors = lint_notebook(filepath, config)
        errors = [(filepath, lineno, name, message) for lineno, name, message in lint_errors]
    return errors


def main() -> None:
    """Execute the linter via a cli invocation."""
    parser = argparse.ArgumentParser(description="Custom Python Linter")
    parser.add_argument("--directory", type=str, help="Directory to scan for Python and Jupyter files")
    parser.add_argument("--file", type=str, help="Single file to scan")
    parser.add_argument("--config", type=str, help="Path to config.toml for configuration", default="mansa/config.toml")
    args = parser.parse_args()

    config = toml.load(args.config)

    files_to_process = []
    if args.file:
        files_to_process.append(args.file)

    if args.directory:
        py_files, ipynb_files = scan_directory(args.directory)
        files_to_process.extend(py_files)
        files_to_process.extend(ipynb_files)

    all_errors = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, filepath, config): filepath for filepath in files_to_process}
        for future in as_completed(futures):
            filepath = futures[future]
            try:
                errors = future.result()
                all_errors.extend(errors)
            except Exception as exc:
                print(f"{filepath} generated an exception: {exc}")

    for filepath, lineno, name, message in all_errors:
        if name:
            print(f"{filepath}:{lineno}: {name}: {message}")
        else:
            print(f"{filepath}:{lineno}: {message}")


if __name__ == "__main__":
    main()
