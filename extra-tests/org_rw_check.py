#!/usr/bin/env python3

import os
import sys

import org_rw

top = sys.argv[1]
count = 0

for root, dirs, files in os.walk(top):
    for name in files:
        if ".org" not in name:
            continue

        path = os.path.join(root, name)
        count += 1
        try:
            org_rw.load(open(path), extra_cautious=True)
        except Exception as err:
            import traceback

            traceback.print_exc()
            print(f"== On {path}")
            sys.exit(1)

print("[OK] Check passed on {} files".format(count))
