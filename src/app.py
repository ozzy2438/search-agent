from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from agent import WorkflowAgent, ResearchError, ReasoningError
import asyncio
import os
from functools import wraps
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set absolute paths for template and static directories
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(os.path.dirname(current_dir), 'templates')
static_dir = os.path.join(os.path.dirname(current_dir), 'static')

app = Flask(__name__,
           template_folder=template_dir,
           static_folder=static_dir,
           static_url_path='/static')
           
CORS(app)

# Get API key from environment
API_KEY = os.getenv("TAVILY_API_KEY")
if not API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

agent = WorkflowAgent(api_key=API_KEY)

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (ResearchError, ReasoningError) as e:
            logger.error(f"API Error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'error_type': e.__class__.__name__
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'error_type': 'ServerError'
            }), 500
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add-task', methods=['POST'])
@handle_errors
def add_task():
    try:
        data = request.get_json()
        logger.info(f"Received task data: {data}")
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data received'
            }), 400
            
        if 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Query is required'
            }), 400
            
        query = data['query']
        if not query.strip():
            return jsonify({
                'status': 'error',
                'message': 'Query cannot be empty'
            }), 400
            
        category = data.get('category', 'general')
        importance = int(data.get('importance', 1))
        
        agent.add_task(query, category, importance)
        logger.info(f"Task added successfully: {query}")
        
        return jsonify({
            'status': 'success',
            'message': 'Task added successfully'
        })
    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/process-tasks', methods=['POST'])
@handle_errors
def process_tasks():
    try:
        logger.info("Processing tasks...")
        results = asyncio.run(agent.process_tasks())
        logger.info(f"Tasks processed successfully: {results}")
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error processing tasks: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/queue-status')
@handle_errors
def queue_status():
    try:
        tasks = agent.get_queue_status()
        logger.info(f"Current queue status: {tasks}")
        return jsonify({
            'status': 'success',
            'queue_size': len(tasks),
            'tasks': tasks
        })
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed'
    }), 405

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    import sys
    port = 5002
    if '--port' in sys.argv:
        try:
            port = int(sys.argv[sys.argv.index('--port') + 1])
        except (IndexError, ValueError):
            pass
    app.run(debug=True, port=port, host='0.0.0.0')
