from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import threading
import time
from services.fraud_detector import FraudDetector
from services.risk_analyzer import RiskAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fraud_detection_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['fraud_detection']
transactions_collection = db['transactions']
users_collection = db['users']
fraud_patterns_collection = db['fraud_patterns']

# Initialize fraud detection services
fraud_detector = FraudDetector(db)
risk_analyzer = RiskAnalyzer(db)

@app.route('/api/process-transaction', methods=['POST'])
def process_transaction():
    try:
        transaction_data = request.json
        
        # Add timestamp
        transaction_data['timestamp'] = datetime.utcnow()
        
        # Analyze transaction for fraud
        fraud_analysis = fraud_detector.analyze_transaction(transaction_data)
        risk_score = risk_analyzer.calculate_risk_score(transaction_data)
        
        # Combine analysis results
        result = {
            'transaction_id': transaction_data.get('transaction_id'),
            'confidence_score': fraud_analysis['confidence_score'],
            'risk_score': risk_score,
            'action': fraud_analysis['recommended_action'],
            'flags': fraud_analysis['flags'],
            'location': transaction_data.get('location', {}),
            'amount': transaction_data.get('amount'),
            'timestamp': transaction_data['timestamp'].isoformat()
        }
        
        # Store transaction
        transactions_collection.insert_one({
            **transaction_data,
            'analysis_result': result
        })
        
        # Emit real-time update to dashboard
        socketio.emit('transaction_update', result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    try:
        # Get recent transactions
        recent_transactions = list(transactions_collection.find(
            {'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=24)}}
        ).sort('timestamp', -1).limit(100))
        
        # Convert ObjectId to string for JSON serialization
        for transaction in recent_transactions:
            transaction['_id'] = str(transaction['_id'])
            transaction['timestamp'] = transaction['timestamp'].isoformat()
        
        # Get fraud statistics
        fraud_stats = {
            'total_transactions': transactions_collection.count_documents({}),
            'flagged_transactions': transactions_collection.count_documents({
                'analysis_result.action': {'$in': ['flag', 'block']}
            }),
            'blocked_transactions': transactions_collection.count_documents({
                'analysis_result.action': 'block'
            })
        }
        
        return jsonify({
            'recent_transactions': recent_transactions,
            'fraud_stats': fraud_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/heat-map-data', methods=['GET'])
def get_heat_map_data():
    try:
        # Aggregate fraud attempts by location
        pipeline = [
            {
                '$match': {
                    'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=24)},
                    'analysis_result.risk_score': {'$gte': 0.7}
                }
            },
            {
                '$group': {
                    '_id': {
                        'country': '$location.country',
                        'city': '$location.city',
                        'lat': '$location.lat',
                        'lng': '$location.lng'
                    },
                    'fraud_count': {'$sum': 1},
                    'avg_risk_score': {'$avg': '$analysis_result.risk_score'}
                }
            }
        ]
        
        heat_map_data = list(transactions_collection.aggregate(pipeline))
        
        return jsonify(heat_map_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simulate real-time transaction generation for demo
def generate_demo_transactions():
    import random
    
    demo_locations = [
        {'country': 'USA', 'city': 'New York', 'lat': 40.7128, 'lng': -74.0060},
        {'country': 'UK', 'city': 'London', 'lat': 51.5074, 'lng': -0.1278},
        {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lng': 13.4050},
        {'country': 'France', 'city': 'Paris', 'lat': 48.8566, 'lng': 2.3522},
        {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lng': 139.6503}
    ]
    
    while True:
        time.sleep(random.randint(2, 8))  # Random interval between transactions
        
        transaction = {
            'transaction_id': f"TXN_{int(time.time())}_{random.randint(1000, 9999)}",
            'user_id': f"USER_{random.randint(1000, 9999)}",
            'amount': random.randint(10, 5000),
            'merchant': random.choice(['Amazon', 'Walmart', 'Target', 'Best Buy', 'Unknown Merchant']),
            'location': random.choice(demo_locations),
            'hour': datetime.utcnow().hour,
            'payment_method': random.choice(['credit_card', 'debit_card', 'digital_wallet'])
        }
        
        # Occasionally create suspicious transactions
        if random.random() < 0.2:  # 20% chance of suspicious transaction
            transaction['amount'] = random.randint(2000, 10000)
            transaction['hour'] = random.choice([2, 3, 4, 23, 0, 1])  # Unusual hours
            transaction['merchant'] = 'Unknown Merchant'
        
        # Process transaction
        with app.test_request_context():
            fraud_analysis = fraud_detector.analyze_transaction(transaction)
            risk_score = risk_analyzer.calculate_risk_score(transaction)
            
            result = {
                'transaction_id': transaction['transaction_id'],
                'confidence_score': fraud_analysis['confidence_score'],
                'risk_score': risk_score,
                'action': fraud_analysis['recommended_action'],
                'flags': fraud_analysis['flags'],
                'location': transaction['location'],
                'amount': transaction['amount'],
                'timestamp': datetime.utcnow().isoformat(),
                'merchant': transaction['merchant']
            }
            
            transaction['timestamp'] = datetime.utcnow()
            transactions_collection.insert_one({
                **transaction,
                'analysis_result': result
            })
            
            socketio.emit('transaction_update', result)

# Start demo transaction generation in background
demo_thread = threading.Thread(target=generate_demo_transactions, daemon=True)
demo_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
