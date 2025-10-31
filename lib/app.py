"""
Unified Flask API for Exercise Detection Application.
Consolidates all routes and endpoints into a single application.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import logging
from datetime import datetime
import config

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for tracking active exercise
active_exercise = {
    'type': None,
    'thread': None,
    'running': False,
    'start_time': None,
    'rep_count': 0
}

# Import exercise modules
try:
    import exercises.bicep as bicep_module
    import exercises.lateral_raises as lateral_raises_module
    import exercises.shoulder as shoulder_module
    import exercises.crunches as crunches_module
except ImportError:
    # Fallback to old module structure
    import bicep as bicep_module
    import lateral_raises as lateral_raises_module
    import shoulder as shoulder_module
    import crunches as crunches_module


@app.route('/')
def home():
    """Welcome endpoint."""
    return jsonify({
        "message": "Welcome to the Exercise Detection API",
        "version": "1.0.0",
        "endpoints": {
            "exercises": ["/lateral_raises", "/shoulder_press", "/crunches", "/bicep_curls"],
            "control": ["/status", "/stop"],
            "health": ["/health"]
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_exercise": active_exercise['type'],
        "running": active_exercise['running']
    }), 200


@app.route('/status', methods=['GET'])
def get_status():
    """Get current exercise status."""
    return jsonify({
        "active_exercise": active_exercise['type'],
        "running": active_exercise['running'],
        "rep_count": active_exercise['rep_count'],
        "start_time": active_exercise['start_time'].isoformat() if active_exercise['start_time'] else None
    }), 200


@app.route('/stop', methods=['POST'])
def stop_exercise():
    """Stop the currently running exercise."""
    if not active_exercise['running']:
        return jsonify({
            "status": "No exercise is currently running"
        }), 400
    
    active_exercise['running'] = False
    exercise_type = active_exercise['type']
    active_exercise['type'] = None
    active_exercise['start_time'] = None
    
    logger.info(f"Stopped exercise: {exercise_type}")
    
    return jsonify({
        "status": "Exercise stopped",
        "exercise": exercise_type,
        "final_rep_count": active_exercise['rep_count']
    }), 200


def start_exercise_thread(exercise_type, exercise_function):
    """Helper function to start an exercise in a separate thread."""
    if active_exercise['running']:
        logger.warning(f"Exercise {active_exercise['type']} is already running")
        return False
    
    active_exercise['type'] = exercise_type
    active_exercise['running'] = True
    active_exercise['start_time'] = datetime.now()
    active_exercise['rep_count'] = 0
    
    thread = threading.Thread(target=exercise_function, daemon=True)
    active_exercise['thread'] = thread
    thread.start()
    
    logger.info(f"Started exercise: {exercise_type}")
    return True


@app.route('/lateral_raises', methods=['POST'])
def lateral_raises_endpoint():
    """Start lateral raises detection."""
    try:
        if not start_exercise_thread('lateral_raises', lateral_raises_module.lateral_raises):
            return jsonify({
                "error": "Another exercise is already running"
            }), 409
        
        return jsonify({
            "status": "Lateral Raises Detection started",
            "message": "Position yourself in front of the camera"
        }), 200
    except Exception as e:
        logger.error(f"Error starting lateral raises: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to start lateral raises detection",
            "message": str(e)
        }), 500


@app.route('/shoulder_press', methods=['POST'])
def shoulder_press_endpoint():
    """Start shoulder press detection."""
    try:
        if not start_exercise_thread('shoulder_press', shoulder_module.shoulder_press):
            return jsonify({
                "error": "Another exercise is already running"
            }), 409
        
        return jsonify({
            "status": "Shoulder Press Detection started",
            "message": "Position yourself in front of the camera"
        }), 200
    except Exception as e:
        logger.error(f"Error starting shoulder press: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to start shoulder press detection",
            "message": str(e)
        }), 500


@app.route('/crunches', methods=['POST'])
def crunches_endpoint():
    """Start crunches detection."""
    try:
        if not start_exercise_thread('crunches', crunches_module.crunches):
            return jsonify({
                "error": "Another exercise is already running"
            }), 409
        
        return jsonify({
            "status": "Crunches Detection started",
            "message": "Position yourself in front of the camera"
        }), 200
    except Exception as e:
        logger.error(f"Error starting crunches: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to start crunches detection",
            "message": str(e)
        }), 500


@app.route('/bicep_curls', methods=['POST'])
def bicep_curls_endpoint():
    """Start bicep curls detection."""
    try:
        if not start_exercise_thread('bicep_curls', bicep_module.bicep_curl_detection):
            return jsonify({
                "error": "Another exercise is already running"
            }), 409
        
        return jsonify({
            "status": "Bicep Curl Detection started",
            "message": "Position yourself in front of the camera"
        }), 200
    except Exception as e:
        logger.error(f"Error starting bicep curls: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to start bicep curl detection",
            "message": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting Flask server on {config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )

