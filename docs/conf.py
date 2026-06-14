# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

sys.path.append(os.path.abspath(".."))

# --- Temp const for escape init Pydantic validation ---
os.environ["DB_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/db"
os.environ["JWT_SECRET"] = "documentation_build_dummy_secret_key_1234567890"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_MINUTES"] = "11111"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "33"
os.environ["MAIL_USERNAME"] = "dummy@example.com"
os.environ["MAIL_PASSWORD"] = "dummy_password"
os.environ["MAIL_FROM"] = "dummy@example.com"
os.environ["MAIL_PORT"] = "465"
os.environ["MAIL_SERVER"] = "smtp.example.com"
os.environ["CLOUDINARY_NAME"] = "dummy_cloud"
os.environ["CLOUDINARY_API_KEY"] = "123456789012345"
os.environ["CLOUDINARY_API_SECRET"] = "dummy_secret"

project = "REST API"
copyright = "2026, Artem Terzi"
author = "Artem Terzi"
release = "0.1.3"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "nature"
html_static_path = ["_static"]
