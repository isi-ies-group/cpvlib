# -*- coding: utf-8 -*-

from setuptools import setup

setup_args = dict(
    name="cpvlib",
    version="0.1.0",
    url='http://github.com/isi-ies-group/cpvlib',
    author="IES-UPM ISI Group",
    author_email="info@ies.upm.es",
    description="CPV Systems modeling",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
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
            'sphinx_rtd_theme==0.5.0', 'sphinx-gallery']
}

TESTS_REQUIRE = ['pytest', 'pytest-mock']

if __name__ == '__main__':
    setup(
    **setup_args,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    tests_require=TESTS_REQUIRE
    )