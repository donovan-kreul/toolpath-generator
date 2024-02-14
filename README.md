# toolpath-generator

Creates user-defined point clouds which define tool paths along a surface. Uses Mitsuba 3 for rendering.

**Files required:** 
1. Object mesh (.obj format)
2. Setup file (.py)

See setups/template.py for a template setup file. Can use methods from pointsGen.py and/or implement custom functionality.

**Usage:** `python3 createRender.py [rendername] [setup-filename.py]`
