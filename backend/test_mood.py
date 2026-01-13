from models.mood_detector import MoodDetector
import os

def test_mood_detector():
    print("Testing MoodDetector...")
    
    # Initialize
    md = MoodDetector()
    
    # Test 1: Detect mood from input
    print("\nTest 1: Detect mood from input (Happy)")
    result = md.detect_mood_from_input(1, 'happy')
    print(f"Result: {result}")
    
    # Test 2: Get current mood
    print("\nTest 2: Get current mood")
    current = md.get_current_mood(1)
    print(f"Current Mood: {current}")
    
    # Test 3: Get mood history
    print("\nTest 3: Get mood history")
    history = md.get_mood_history(1)
    print(f"History entries: {len(history)}")
    if history:
        print(f"Latest entry: {history[0]}")

    # Test 4: Infer mood
    print("\nTest 4: Infer mood from behavior")
    inferred = md.infer_mood_from_behavior(1, {"genre": "drama"})
    print(f"Inferred mood for 'drama': {inferred}")

if __name__ == "__main__":
    test_mood_detector()
