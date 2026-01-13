from flask import Flask, jsonify
from flask_cors import CORS
import logging

# Import blueprints
from routes.contextual_recommend import contextual_bp

# Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app) # Allow all origins for prototype
    
    # Register Layout/Routes
    app.register_blueprint(contextual_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "Content Recommendation API is running",
            "status": "active",
            "version": "1.0.0"
        })
        
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404
        
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
        
    return app

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Flask Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
