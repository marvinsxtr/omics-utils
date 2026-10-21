import os
import sys

# Repo root, so that omics_utils is importable without the container's PYTHONPATH.
sys.path.insert(0, os.path.abspath("../.."))  # noqa: PTH100

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "omics-utils"
copyright = "2025, The BIFOLD Pathomics Team"  # noqa: A001
author = "The BIFOLD Pathomics Team"
release = "v0.0.24"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
autosummary_generate = True
autosummary_ignore_module_all = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_sidebars = {"readme": []}
html_title = "🧬 omics-utils"
