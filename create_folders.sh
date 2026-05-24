#!/bin/bash
find 0[1-9]_*/ -type d | while read -r d; do echo "# $(basename "$d")" > "$d/README.md" && echo "Created: $d/README.md"; done
