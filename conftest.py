"""Make the repo root importable so tests can `import glyphgen` etc."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
