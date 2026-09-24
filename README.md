# ONDE-format

## Generalities
Specification of the ONDE (**Open Non Destructive Evaluation**) Format

This specification of the ONDE format results from a joint initiative by COFREND and EPRI to define a specification of open and efficient NDE formats in order to facilitate interoperability between software and to ensure the ability to read data in the long term.

In order to achieve these objectives, it is based on the HDF5 library.

The present repository contains the Single Source of Truth (SSOT) for the data model in the `class_definitions/` directory. The specification is defined through a series of YAML files. Each YAML file contains both the machine-readable metadata defining the HDF5 structure as well as the human-readable Markdown narrative explaining the concepts.

The human-readable version resulting from this SSOT is available here : [https://cofrend.github.io/ONDE-format/](https://cofrend.github.io/ONDE-format/).
This version of the specification is the latest one available.

At this stage, only ultrasound testing is considered.
It will be completed in the future by an extension to Eddy Current testing and by python tools allowing to check the compliance of a file to the specification.

## Local Documentation Rendering

The documentation is built using MkDocs. You can render it locally using the provided generation script:

1. Install the required dependencies:
   ```bash
   pip install pydantic pyyaml mkdocs-material
   ```

2. Run the generation script:
   ```bash
   python tools/generate_docs.py
   ```

The generated documentation site will be available in the `build/docs/site/` directory.

## CSV Export for Automated Tooling

While the Single Source of Truth for the specification is defined using the individual YAML files in the `class_definitions/` directory, navigating multiple YAML files can become cumbersome for quick import or validation purposes in automated tooling.

For simplified use in these scenarios, we provide a unified CSV export of the data model. You can download the latest generated CSV file directly from the documentation site here: [https://COFREND.github.io/ONDE-format/ONDE_fields.csv](https://COFREND.github.io/ONDE-format/ONDE_fields.csv).

You can also generate the CSV file manually at any time by running:
```bash
python tools/generate_csv.py
```

The generated CSV file will be available at `build/ONDE_fields.csv` locally.

## Instructions for contributors

New proposals can be submitted by using the github *Issue* functionality. Note that when modifying the specification, you should edit the corresponding `.yaml` files in the `class_definitions/` directory.

The git branches are created with the following conventions:
* `main` is the branch containing the latest version of the specification
* `next_minor` is the branch containing bug corrections or minor evolutions that are intended to become the next version of the specification
* `next_major` is a working branch containing major evolutions

When a minor version is created, changes are merged from `next_minor` into `main` and from `main` into `next_major`.
When a major version is created, changes are merged from `next_major` into `main` and from `main` into `next_minor`.

Branches related to an issue are named in one of the following manners:
* `[Issue_short_title]_[issue_number]`
* `[Common theme]` (for multiple issues)

They are based on `next_minor` or `next_major` according to the type of issue.
