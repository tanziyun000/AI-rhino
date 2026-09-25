# Review Grasshopper Python Prototype

## Goal

Review the current pure-Python prototype for correctness, robustness, and Grasshopper readiness.

## Focus areas

1. Rectangle geometry correctness
2. BSP-style partition quality
3. Room assignment correctness
4. Rule checks and warnings
5. Score behavior
6. Batch runner error handling
7. JSON output structure

## Questions to answer

- Are there any hidden assumptions that will break on non-rectangular boundaries?
- Are warnings too weak or too strict?
- Is the score formula meaningful enough for MVP comparison?
- Which functions should be wrapped for Grasshopper Python next?
