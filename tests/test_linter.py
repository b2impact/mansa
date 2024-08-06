import ast  # noqa: F401
import textwrap

import pytest  # noqa: F401

from mansa.linter import lint_code, lint_notebook  # noqa: F401

# Sample configuration for tests
config = {
    "target_classes": {
        "AmlComputeProvisioningConfiguration": "E001",
        "ComputeInstance": "E002",
        "ComputeCluster": "E003",
        "BatchDeployment": "E004",
        "BatchEndpoint": "E005",
        "ManagedOnlineEndpoint": "E006",
        "ModelBatchDeployment": "E007",
        "OnlineDeployment": "E008",
        "OnlineEndpoint": "E009",
        "PipelineComponent": "E010",
        "PipelineComponentBatchDeployment": "E011",
        "Deployment": "E012",
        "Jobs": "E013",
        "AzureOpenAIDeployment": "E014",
        "ServerlessEndpoint": "E015",
    }
}


# Test cases
def test_missing_tags_argument():
    code = """
    instance = ComputeInstance(name='my_instance')
    """
    code = textwrap.dedent(code)
    errors = lint_code(code, config)
    assert len(errors) == 1
    assert errors[0][2] == "E002: 'ComputeInstance' instantiation is missing 'tags' argument"


def test_invalid_tags_format():
    code = """
    instance = ComputeInstance(name='my_instance', tags='invalid')
    """
    code = textwrap.dedent(code)
    errors = lint_code(code, config)
    assert len(errors) == 1
    print(errors)
    assert errors[0][2] == "Tags argument is not a valid dictionary"


def test_invalid_tag_key():
    code = """
    instance = ComputeInstance(name='my_instance', tags={'invalid_key': 'value'})
    """
    code = textwrap.dedent(code)
    errors = lint_code(code, config)
    print(errors)
    assert len(errors) == 1
    assert errors[0][2] == "Invalid tag key 'invalid_key'"


def test_invalid_tag_value():
    code = """
    instance = ComputeInstance(name='my_instance', tags={'environment': 'invalid'})
    """
    code = textwrap.dedent(code)
    errors = lint_code(code, config)
    print(errors)
    assert len(errors) == 1
    assert errors[0][2] == "Invalid value 'invalid' for key 'environment'"


def test_valid_tags():
    code = """
    instance = ComputeInstance(name='my_instance', tags={'environment': 'dev',
    'businessOwner': 'lukasthegreat@b2-impact.com',
    'technicalOwner': 'da-modelling', 'businesUnit': 'swe', 'source': 'amlsdk2',
    'ismsClassification': 'M'})
    """
    code = textwrap.dedent(code)
    errors = lint_code(code, config)
    assert len(errors) == 0


def test_lint_notebook():
    notebook_content = {"cells": [{"cell_type": "code", "source": ["instance = ComputeInstance(name='my_instance')"]}]}
    with open("tests/test_notebook.ipynb", "w") as f:
        import json

        json.dump(notebook_content, f)
    errors = lint_notebook("tests/test_notebook.ipynb", config)
    assert len(errors) == 1
    assert errors[0][2] == "E002: 'ComputeInstance' instantiation is missing 'tags' argument"


# Clean up test notebook file after tests
def teardown_module(module):
    import os

    if os.path.exists("tests/test_notebook.ipynb"):
        os.remove("tests/test_notebook.ipynb")
