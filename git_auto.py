#!/usr/bin/env python3
"""
Backward-compatibility entrypoint for Autopush.
Redirects to autopush.cli.main().
"""

import sys
from autopush.cli import main

if __name__ == "__main__":
    main()
