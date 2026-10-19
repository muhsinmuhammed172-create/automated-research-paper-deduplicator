
from src.similarity import calculate_title_similarity

title_a = "Machine Learning for Disease Prediction"
title_b = "Machine Learning-Based Disease Prediction"

score = calculate_title_similarity(title_a, title_b)

print("Title A:", title_a)
print("Title B:", title_b)
print("Similarity score:", score)
