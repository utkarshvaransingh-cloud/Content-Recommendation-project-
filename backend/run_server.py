from app import app
import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("-------------------------------------------------------")
    print("   Starting Content Recommendation Backend Server")
    print("   API available at: http://localhost:5000/api")
    print("-------------------------------------------------------")
    app.run(host='127.0.0.1', port=5000, debug=False)
