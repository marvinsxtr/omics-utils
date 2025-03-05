import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Omics Utils'
copyright = '2025, The Omics Team'
author = 'The Omics Team'
release = 'v0.0.13'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',	
    'sphinx.ext.napoleon',	
]

# autodoc_mock_imports = ['numpy', 'dask', 'dask_jobqueue', 'scikit-learn', 'ml_project_template', 'hydra_zen']
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
