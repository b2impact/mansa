[![mansa-ci-pipeline](https://github.com/b2impact/mansa/actions/workflows/ci-pipeline.yaml/badge.svg)](https://github.com/b2impact/mansa/actions/workflows/ci-pipeline.yaml)![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

# Mansa - a FinOps friendly linter

<p align="center">
<img src="/docs/images/meme.jpg">
</p>

FinOps is an operational framework and cultural practice that enhances the business value derived from cloud technology. It promotes data-driven decision-making in a timely manner and fosters financial responsibility. It gets achieved through collaboration among engineering, finance, and business teams.

FinOps is a discipline that combines financial management principles with cloud engineering and operations to provide organizations with a better understanding of their cloud spending. It also helps them make informed decisions on how to allocate and manage their cloud costs. The goal of FinOps isn't to save money, but to maximize revenue or business value through the cloud. It helps to enable organizations to control cloud spending while maintaining the level of performance, reliability, and security needed to support their business operations.

All of the cloud service providers also allow for the use of tags which can be applied as metadata to most individual resources, and which then appear in the detailed billing reports providing cost and usage data when turned on by the user. Tagging is an essential pre-requirement for FinOps implementation.

Mansa is a lintin tool used internally at B2-Impact to enforce cost-tagging at build time as part of our standard CI-CD pipelines for Azure Machine Learning Resources.

# Why Mansa?

Usually IOps teams deploy their infrastructure using terraform/bicep/cdk languages. However in most of the cases the IOps teams are only in charge of deploying the infrastructure "container" that an application will use. In the case of Machine Learning this situation is even more common as the recursive experimental nature of AI applications makes quite common the fact that we do not know which deployment configuration will be best during the development phase.

Besides a lot of MLOps processes as creation of ML pipelines, compute clusters, job launching, inference endpoints etc... are invoked via python SDKs and not terraform code.

Because of that we decided to create Mansa. Mansa scans all your python code in search of classes that accept the tags arguments, currently these classes are configurable with a config.toml file as we have not been able to come up with a better method that is as simple as this.

Mansa also looks that the tags contains a certain key-value pairs with allowed values. Currently this is hardcoded in the code but we plan to make this configurable via a section in the config.toml file.

## Why this name?

[Mansa Musa](https://en.wikipedia.org/wiki/Mansa_Musa) was the 9th Mansa of the Mali Empire, he was one of the richest people in history. According to some research \[1\] he was so rich that he was generating inflation wherever he went. His wealth was not measurable and therefore neither his spending. We took inspiration of his story for the naming of this package as we believe that is important to keep track of cost and we do not want to contribute to the [cloud cost inflation phenomena](https://www.techtarget.com/searchcio/news/366570542/Cloud-costs-continue-to-rise-in-2024#:~:text=The%20cloud%20inflation%20trend%20looks,pattern%20of%20rising%20cloud%20costs.).

# Usage guide

Just run: 

``` bash
mansa --directory .
mansa --file mypythonfile.py
```
If you want to use your custom config.toml file you can use:

``` bash
mansa --directory . --config myfile.toml
mansa --file mypythonfile.py --config myfile.toml
```

# Build Instructions

1.  Install poetry via the [oficial installer](https://python-poetry.org/docs/#installing-with-the-official-installer):

    ``` bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2.  Clone this repository with:

    ``` bash
    git clone https://github.com/b2impact/mansa.git
    ```
3.  Ensure poetry is using the correct virtual environment. You can activate the environment manually with:

    ``` bash
    poetry shell
    ```

4.  Install dependencies and build the package:

    ``` bash
    poetry install
    ```

5.  Build the package:

    ``` bash
    poetry build
    ```

# Development guidelines

As usual, we stick to [TBD](https://trunkbaseddevelopment.com/), Create your own branch according to the following guidelines:

-   {type_of_branch}/{namefirstlettersurnamefirstlettersurnamesecondletter}/{change_name}

-   Being type of branch:

    -   feat (of feature).

    -   bugfix/fix (to fix a bug).

    -   enh/improvement (for enhancement, usually runtime performance).

### Run tests

To run the tests, run the following in the root directory of the project:

``` bash
poetry run pytest
```

Or to run multiversion tests with linting included:

``` bash
poetry run tox
```

To install tox we recommend using pipx as:

``` bash
pipx install tox
```

### Introducing dependencies

Please install dependencies via:

``` bash
poetry add {dependency-name}=={version}
```

When doing that your pyproject.toml file will be automatically updated as well as the lock files.

### References

\[1\] Goodwin, A. J. H. (1957). The Medieval Empire of Ghana. *The South African Archaeological Bulletin*, *12*(47), 108–112. https://doi.org/10.2307/3886971
