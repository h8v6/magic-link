# API Reference

Use Sphinx with MyST to generate API documentation for the project.

## 1. Install Documentation Tooling

```bash
pip install sphinx myst-parser sphinx-autodoc-typehints
```

## 2. Scaffold Sphinx Project

```bash
sphinx-quickstart docs/reference --no-sep --dot _ --project "magic_link" --author "magic_link maintainers" --ext-autodoc --ext-autosummary
```

Enable MyST and autodoc inside `docs/reference/conf.py`:

```python
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
]
autosummary_generate = True
```

## 3. Autodoc Targets

Create a `modules.md` file that pulls in each module using MyST directives:

```{eval-rst}
.. automodule:: magic_link.config
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: magic_link.token_engine
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: magic_link.interfaces
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: magic_link.storage.in_memory
   :members:
```

```{eval-rst}
.. automodule:: magic_link.storage.sqlalchemy
   :members:
```

```{eval-rst}
.. automodule:: magic_link.storage.redis
   :members:
```

```{eval-rst}
.. automodule:: magic_link.mailer.smtp
   :members:
```

```{eval-rst}
.. automodule:: magic_link.errors
   :members:
```

## 4. Build the Documentation

```bash
sphinx-build docs/reference docs/reference/_build
```

The generated HTML will include all public classes, methods, and exceptions from the library.
