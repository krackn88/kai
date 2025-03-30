#!/usr/bin/env python3
"""
Run all tests for the Anthropic-powered Agent
"""

import unittest
import sys

if __name__ == "__main__":
    # Discover and run all tests
    test_suite = unittest.defaultTestLoader.discover("tests")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero status if tests failed
    if not result.wasSuccessful():
        sys.exit(1)