from models.time_analyzer import TimeOfDayAnalyzer
from datetime import datetime

def test_time_analyzer():
    print("Testing TimeOfDayAnalyzer...")
    
    ta = TimeOfDayAnalyzer()
    
    # Test 1: Get current period
    print("\nTest 1: Current Period Info")
    current = ta.get_current_period()
    print(f"Current: {current}")
    
    # Test 2: Check specfiic hours
    print("\nTest 2: Period by Hour")
    hours_to_test = [8, 14, 19, 23]
    for h in hours_to_test:
        p = ta.get_period_by_hour(h)
        print(f"Hour {h}: {p}")
        
    # Test 3: Genre Scoring
    print("\nTest 3: Genre Scoring (assuming 'afternoon' or 'evening' context)")
    genres = ["action", "documentary", "horror"]
    for g in genres:
        score = ta.get_genre_score_for_time(g)
        print(f"Genre '{g}': {score}")
        
    # Test 4: Duration check
    print("\nTest 4: Duration Check")
    durations = [30, 100, 200]
    for d in durations:
        is_opt = ta.is_optimal_time_for_duration(d)
        print(f"{d} min optimal? {is_opt}")

if __name__ == "__main__":
    test_time_analyzer()
