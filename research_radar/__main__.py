import sys

if sys.version_info < (3, 11):
    print(
        f"Research Radar requires Python 3.11 or newer; current version is {sys.version.split()[0]}.",
        file=sys.stderr,
    )
    raise SystemExit(2)

from .cli import main

raise SystemExit(main())
