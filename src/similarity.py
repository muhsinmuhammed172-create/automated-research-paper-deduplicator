
from rapidfuzz import fuzz


def calculate_title_similarity(title_a, title_b):
    """Calculate title similarity on a scale from 0 to 100."""
    if not title_a or not title_b:
        return 0

    return fuzz.ratio(
        str(title_a).strip().lower(),
        str(title_b).strip().lower()
    )
