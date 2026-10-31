
"""Interactive duplicate-candidate review.

Usage
-----
python review.py crossref
python review.py synthetic
python review.py plant_test
"""

import sys
from src.verification import review_queue

if __name__ == "__main__":
    dataset = sys.argv[1].lower() if len(sys.argv) > 1 else "synthetic"
    review_queue(dataset)
