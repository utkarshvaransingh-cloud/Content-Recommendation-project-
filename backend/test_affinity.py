from models.mood_content_affinity import MoodContentAffinity

def test_affinity():
    print("Testing MoodContentAffinity...")
    
    ma = MoodContentAffinity()
    
    # Test 1: Affinity Score
    print("\nTest 1: Affinity Score")
    s1 = ma.get_affinity_score("happy", "comedy")
    s2 = ma.get_affinity_score("happy", "horror")
    print(f"Happy + Comedy: {s1}")
    print(f"Happy + Horror: {s2}")
    
    # Test 2: Best Genres
    print("\nTest 2: Best Genres for 'Sad'")
    best = ma.get_best_genres_for_mood("sad", 3)
    for b in best:
        print(f"{b['genre']}: {b['score']}")
        
    # Test 3: Score Content
    print("\nTest 3: Score Content Item")
    item = {"title": "Funny Movie", "genres": ["Comedy", "Adventure"]} # Happy affinity: comedy=0.95, adventure=0.85 -> avg 0.90
    score = ma.score_content(item, "happy")
    print(f"Content Score for Happy: {score}")
    
    # Test 4: Rank Recommendations
    print("\nTest 4: Rank Recommendations")
    recs = [
        {"title": "Scary Movie", "genres": ["Horror"]},
        {"title": "Fun Movie", "genres": ["Comedy"]}
    ]
    ranked = ma.rank_recommendations_by_mood(recs, "happy")
    print(f"Top Recommendation for Happy: {ranked[0]['title']}")

if __name__ == "__main__":
    test_affinity()
