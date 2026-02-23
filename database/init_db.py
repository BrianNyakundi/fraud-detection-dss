from pymongo import MongoClient
from datetime import datetime, timedelta
import random

def initialize_database():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fraud_detection']
    
    # Clear existing collections
    db.transactions.drop()
    db.users.drop()
    db.fraud_patterns.drop()
    
    # Create collections with indexes
    transactions = db.transactions
    users = db.users
    fraud_patterns = db.fraud_patterns
    
    # Create indexes for better performance
    transactions.create_index([('user_id', 1), ('timestamp', -1)])
    transactions.create_index([('timestamp', -1)])
    transactions.create_index([('analysis_result.risk_score', -1)])
    transactions.create_index([('location.country', 1)])
    
    users.create_index([('user_id', 1)])
    
    # Insert sample fraud patterns
    sample_patterns = [
        {
            'pattern_id': 'HIGH_AMOUNT_NIGHT',
            'description': 'High amount transactions during night hours',
            'risk_weight': 0.8,
            'conditions': {
                'amount': {'$gt': 2000},
                'hour': {'$in': [22, 23, 0, 1, 2, 3, 4, 5]}
            }
        },
        {
            'pattern_id': 'RAPID_TRANSACTIONS',
            'description': 'Multiple transactions in short time period',
            'risk_weight': 0.9,
            'conditions': {
                'transaction_count_1h': {'$gte': 5}
            }
        },
        {
            'pattern_id': 'NEW_LOCATION',
            'description': 'Transaction from new geographical location',
            'risk_weight': 0.6,
            'conditions': {
                'location_seen_before': False
            }
        },
        {
            'pattern_id': 'UNKNOWN_MERCHANT',
            'description': 'Transaction with unknown or suspicious merchant',
            'risk_weight': 0.7,
            'conditions': {
                'merchant': {'$in': ['Unknown Merchant', 'Suspicious Shop', '']}
            }
        }
    ]
    
    fraud_patterns.insert_many(sample_patterns)
    
    # Insert sample users
    sample_users = []
    for i in range(1000, 2000):
        user = {
            'user_id': f'USER_{i}',
            'created_at': datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            'profile': {
                'typical_amount_range': [50, 500],
                'common_locations': [
                    {'country': 'USA', 'city': 'New York'},
                    {'country': 'USA', 'city': 'Los Angeles'}
                ],
                'common_hours': list(range(9, 22)),  # 9 AM to 9 PM
                'preferred_merchants': ['Amazon', 'Walmart', 'Target']
            },
            'risk_score': random.uniform(0.1, 0.3)  # Most users are low risk
        }
        sample_users.append(user)
    
    users.insert_many(sample_users)
    
    print("Database initialized successfully!")
    print(f"Created {len(sample_patterns)} fraud patterns")
    print(f"Created {len(sample_users)} sample users")
    
    return db

if __name__ == "__main__":
    initialize_database()
