# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'cpvlib'
copyright = '2021, ISI-IES group at UPM'
author = 'ISI-IES group at UPM'

# The full version, including alpha/beta/rc tags
from pkg_resources import get_distribution
release = get_distribution('cpvlib').version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['IPython.sphinxext.ipython_console_highlighting',
              'IPython.sphinxext.ipython_directive',
              'sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              'sphinxcontrib.apidoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.viewcode',
]

napoleon_use_rtype = False  # group rtype on same line together with return

# APIdoc auto
apidoc_module_dir = '../../cpvlib'
apidoc_output_dir = '.'
apidoc_excluded_paths = ['tests', 'StaticHybridSystem_tmy.py', 'module_parameters.py']
apidoc_separate_modules = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# %% helper functions for intelligent "View on Github" linking
# based on
# https://gist.github.com/flying-sheep/b65875c0ce965fbdd1d9e5d0b9851ef1


def get_obj_module(qualname):
    """
    Get a module/class/attribute and its original module by qualname.
    Useful for looking up the original location when a function is imported
    into an __init__.py
    Examples
    --------
    >>> func, mod = get_obj_module("pvlib.iotools.read_midc")
    >>> mod.__name__
    'pvlib.iotools.midc'
    """
    modname = qualname
    classname = None
    attrname = None
    while modname not in sys.modules:
        attrname = classname
        modname, classname = modname.rsplit('.', 1)

    # retrieve object and find original module name
    if classname:
        cls = getattr(sys.modules[modname], classname)
        modname = cls.__module__
        obj = getattr(cls, attrname) if attrname else cls
    else:
        obj = None

    return obj, sys.modules[modname]


def get_linenos(obj):
    """Get an object’s line numbers in its source code file"""
    try:
        lines, start = inspect.getsourcelines(obj)
    except TypeError:  # obj is an attribute or None
        return None, None
    except OSError:  # obj listing cannot be found
        # This happens for methods that are not explicitly defined
        # such as the __init__ method for a dataclass
        return None, None
    else:
        return start, start + len(lines) - 1


def make_github_url(pagename):
    """
    Generate the appropriate GH link for a given docs page.  This function
    is intended for use in sphinx template files.
    The target URL is built differently based on the type of page.  Sphinx
    provides templates with a built-in `pagename` variable that is the path
    at the end of the URL, without the extension.  For instance,
    https://pvlib-python.rtfd.org/en/stable/auto_examples/plot_singlediode.html
    will have pagename = "auto_examples/plot_singlediode".
    """

    URL_BASE = "https://github.com/pvlib/pvlib-python/blob/master/"

    # is it a gallery page?
    if any(d in pagename for d in sphinx_gallery_conf['gallery_dirs']):
        if pagename.split("/")[-1] == "index":
            example_file = "README.rst"
        else:
            example_file = pagename.split("/")[-1] + ".py"
        target_url = URL_BASE + "docs/examples/" + example_file

    # is it an API autogen page?
    elif "generated" in pagename:
        # pagename looks like "generated/pvlib.location.Location"
        qualname = pagename.split("/")[-1]
        obj, module = get_obj_module(qualname)
        path = module.__name__.replace(".", "/") + ".py"
        target_url = URL_BASE + path
        # add line numbers if possible:
        start, end = get_linenos(obj)
        if start and end:
            target_url += f'#L{start}-L{end}'

    # Just a normal source RST page
    else:
        target_url = URL_BASE + "docs/sphinx/source/" + pagename + ".rst"

    return target_url


# variables to pass into the HTML templating engine; these are accessible from
# _templates/breadcrumbs.html
html_context = {
    'make_github_url': make_github_url,
}