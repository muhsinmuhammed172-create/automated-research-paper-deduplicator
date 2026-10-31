
from rapidfuzz import fuzz


def calculate_title_similarity(title_a: str, title_b: str) -> float:
    """Calculate title similarity on a scale from 0 to 100.

    Uses ``token_sort_ratio`` so that word-order variations in titles
    (e.g. "Deep Learning for Plant Disease Detection" vs
    "Plant Disease Detection Using Deep Learning") score correctly,
    unlike the character-level ``fuzz.ratio``.
    """
    if not title_a or not title_b:
        return 0.0

    return fuzz.token_sort_ratio(
        str(title_a).strip().lower(),
        str(title_b).strip().lower(),
    )
