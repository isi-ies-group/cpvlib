1. Push commits
    - Each push creates a new dev version number as num.devXX
    - GH Actions uploads it to TestPyPI
2. Prepare new release
    - Update example (if necessary)
    - Add and fill new changes file v0.1.X.txt in: cpvlib/docs/source/whatsnew/
    - Update cpvlib/docs/source/whatsnew.rst with ".. include::: whatsnew/v0.1.X.txt"
2. Create a release from GH web and tag it with a new tag (0.1.X)
    - GH Actions identifies it as with tag and uploads it to PyPI (in addition to TestPyPI)
