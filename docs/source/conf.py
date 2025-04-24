import os
import sys

# Folder to preprocess.py had to be specified individually.
sys.path.insert(0, os.path.abspath("../../omics_utils"))  # noqa: PTH100
sys.path.insert(0, os.path.abspath("../../../omics-utils"))  # noqa: PTH100


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
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

autosummary_generate = True
templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
