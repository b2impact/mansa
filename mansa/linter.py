import ast
import os
import json
import argparse
import toml
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

VALID_TAGS = {
    "environment": ["sbx", "dev", "pre", "pro", "hub"],
    "businessOwner": re.compile(r".+@.+\..+"),
    "technicalOwner": re.compile(r"[A-Z]{3}-[A-Za-z]+"),
    "businesUnit": re.compile(r"[A-Za-z]{3}"),
    "source": ["terraform", "portal", "amlsdkv2", "amlsdkv1"],
    "ismsClassification": ["L", "M", "H"]
}

class CustomLinter(ast.NodeVisitor):
    def __init__(self, config):
        self.errors = []
        self.target_classes = config.get("target_classes", {})

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.target_classes:
            tags_arg = next((keyword for keyword in node.keywords if keyword.arg == 'tags'), None)
            if not tags_arg:
                error_code = self.target_classes[node.func.id]
                self.errors.append((node.lineno, node.func.id, f"{error_code}: '{node.func.id}' instantiation is missing 'tags' argument"))
            else:
                self.validate_tags(node.lineno, node.func.id, tags_arg.value)
        self.generic_visit(node)

    def validate_tags(self, lineno, class_name, tags_node):
        if not isinstance(tags_node, ast.Dict):
            self.errors.append((lineno, class_name, "Tags argument is not a dictionary"))
            return
        
        for key, value in zip(tags_node.keys, tags_node.values):
            key_str = key.s if isinstance(key, ast.Str) else None
            value_str = value.s if isinstance(value, ast.Str) else None

            if key_str not in VALID_TAGS:
                self.errors.append((lineno, class_name, f"Invalid tag key '{key_str}'"))
                continue

            valid_values = VALID_TAGS[key_str]
            if isinstance(valid_values, list) and value_str not in valid_values:
                self.errors.append((lineno, class_name, f"Invalid value '{value_str}' for key '{key_str}'"))
            elif isinstance(valid_values, re.Pattern) and not valid_values.match(value_str):
                self.errors.append((lineno, class_name, f"Invalid format for value '{value_str}' for key '{key_str}'"))

def lint_code(code, config):
    tree = ast.parse(code)
    linter = CustomLinter(config)
    linter.visit(tree)
    return linter.errors

def lint_notebook(nb_path, config):
    with open(nb_path, 'r') as f:
        notebook = json.load(f)
    errors = []
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            code = ''.join(cell['source'])
            errors.extend(lint_code(code, config))
    return errors

def scan_directory(directory):
    py_files = []
    ipynb_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
            elif file.endswith('.ipynb'):
                ipynb_files.append(os.path.join(root, file))
    return py_files, ipynb_files

def process_file(filepath, config):
    if filepath.endswith('.py'):
        with open(filepath, 'r') as file:
            code = file.read()
        lint_errors = lint_code(code, config)
        errors = [(filepath, lineno, name, message) for lineno, name, message in lint_errors]
    elif filepath.endswith('.ipynb'):
        lint_errors = lint_notebook(filepath, config)
        errors = [(filepath, lineno, name, message) for lineno, name, message in lint_errors]
    return errors

def main():
    parser = argparse.ArgumentParser(description='Custom Python Linter')
    parser.add_argument('directory', type=str, help='Directory to scan for Python and Jupyter files')
    parser.add_argument('--config', type=str, help='Path to config.toml for configuration', default='my_linter/config.toml')
    args = parser.parse_args()

    config_path = args.config
    config = toml.load(config_path)
    
    directory = args.directory
    py_files, ipynb_files = scan_directory(directory)
    all_files = py_files + ipynb_files

    all_errors = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, filepath, config): filepath for filepath in all_files}
        for future in as_completed(futures):
            filepath = futures[future]
            try:
                errors = future.result()
                all_errors.extend(errors)
            except Exception as exc:
                print(f'{filepath} generated an exception: {exc}')
    
    for filepath, lineno, name, message in all_errors:
        if name:
            print(f"{filepath}:{lineno}: {name}: {message}")
        else:
            print(f"{filepath}:{lineno}: {message}")

if __name__ == '__main__':
    main()
