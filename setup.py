# -*- coding: utf-8 -*-

from setuptools import setup

setup_args = dict(
    name="cpvlib",
    version="0.1.0",
    url='http://github.com/isi-ies-group/cpvlib',
    author="IES-UPM ISI Group",
    author_email="ruben.nunez@ies.upm.es",
    description="CPV Systems modeling",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    python_requires='>=3.6',
    packages=['meteocheck'],
    zip_safe=False,
    package_data={'': ['*.ini']},
    include_package_data=True,
)

install_requires = [
    'numpy',
    'pandas',
    'pvlib'
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)