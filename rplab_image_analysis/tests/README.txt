How to run tests using pytest:

1. Open CMD or Terminal

2. Navigate so that the current directory is rplab_image_analysis

3. Run one of the following commands to test:

To run all tests in the tests package, run the following command:

    python -m pytest tests

"python" above can be replaced with the path of any working python interpreter.

To run tests in a specific file, e.g. test_general.py, use the following command:

    python -m pytest tests/test_general.py

To run a specific test, use the -k flag, i.e.:

    python -m pytest -k "test_get_downsample_tuple"

To dump output (such as print statements) to the command prompt, use a trailing
"-s" flag, i.e.:

    python -m pytest -k "test_get_downsample_tuple" -s
