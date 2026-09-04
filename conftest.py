"""Ensures the project root is on sys.path so `app` and `evaluation` are
importable from test modules, regardless of how/where pytest is invoked."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))