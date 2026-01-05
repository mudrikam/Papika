---
applyTo: '**'
---

- All import should be at the top of the file, never put them inside functions or classes unless absolutely necessary.
- Group imports in the following order, with a blank line between each group:
  1. Standard library imports (e.g., os, sys, json)
  2. Third-party library imports (e.g., PySide6, qtawesome)
  3. Local application imports (e.g., from .sidebar_widget import Sidebar)
- Use absolute imports for local application modules whenever possible.
- Avoid wildcard imports (e.g., from module import *) to maintain clarity about which names are being used.
- If found import in the middle of the file, move them to the top unless there is a compelling reason not to.
- Ensure that imports are sorted alphabetically within each group for better readability.