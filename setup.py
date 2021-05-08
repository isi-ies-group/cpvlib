# -*- coding: utf-8 -*-

from setuptools import setup

LONG_DESCRIPTION = """
`cpvlib` is an open source tool that provides a set of functions and classes 
for simulating the performance of concentrator photovoltaic (CPV) systems,
a specific type of photovoltiac systems composed of lenses and/or
mirrors that focus sunlight onto small cells. It makes special emphasys on
static micro CPV systems with internal tracking.

Documentation: http://cpvlib.readthedocs.io
Source code: https://github.com/isi-ies-group/cpvlib
"""

# monkey patch to make compatible setuptools_scm and publishing on TestPyPI
def local_scheme(version):
    return ""

setup_args = dict(
    name="cpvlib",
    use_scm_version={"local_scheme": local_scheme},
    url='http://github.com/isi-ies-group/cpvlib',
    author="IES-UPM ISI Group & cpvlib Development Team",
    author_email="info@ies.upm.es",
    description="CPV Systems modeling",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
    python_requires='>=3.6',
    packages=['cpvlib'],
    zip_safe=False,
    package_data={'': ['*.csv', '*.txt', '*.png', '*.yaml', '*.yml']},
    include_package_data=True,
)

INSTALL_REQUIRES = [
    'numpy==1.20',
    'pandas==1.2',
    'pvlib==0.8',
    'matplotlib==3.3'
]

EXTRAS_REQUIRE = {
    'doc': ['ipython', 'matplotlib', 'sphinx == 3.1.2',
            'sphinx_rtd_theme==0.5.0', 'sphinx-gallery',
            'sphinxcontrib-apidoc']
}

TESTS_REQUIRE = ['pytest', 'pytest-mock']

if __name__ == '__main__':
    setup(
    **setup_args,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    tests_require=TESTS_REQUIRE,
    setup_requires=['setuptools_scm'],
    )
