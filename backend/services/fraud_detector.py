import numpy as np
from datetime import datetime, timedelta
import math

class FraudDetector:
    def __init__(self, db):
        self.db = db
        self.transactions_collection = db['transactions']
        self.users_collection = db['users']
    
    def analyze_transaction(self, transaction):
        flags = []
        risk_factors = []
        
        # Amount-based analysis
        amount_risk = self._analyze_amount(transaction)
        risk_factors.append(amount_risk)
        if amount_risk > 0.7:
            flags.append("High amount transaction")
        
        # Time-based analysis
        time_risk = self._analyze_time(transaction)
        risk_factors.append(time_risk)
        if time_risk > 0.6:
            flags.append("Unusual transaction time")
        
        # Location-based analysis
        location_risk = self._analyze_location(transaction)
        risk_factors.append(location_risk)
        if location_risk > 0.5:
            flags.append("New or suspicious location")
        
        # Frequency analysis
        frequency_risk = self._analyze_frequency(transaction)
        risk_factors.append(frequency_risk)
        if frequency_risk > 0.8:
            flags.append("High frequency transactions")
        
        # Merchant analysis
        merchant_risk = self._analyze_merchant(transaction)
        risk_factors.append(merchant_risk)
        if merchant_risk > 0.7:
            flags.append("Unknown or risky merchant")
        
        # Calculate overall confidence score
        confidence_score = np.mean(risk_factors) if risk_factors else 0.0
        
        # Determine recommended action
        if confidence_score >= 0.8:
            action = "block"
        elif confidence_score >= 0.5:
            action = "flag"
        else:
            action = "approve"
        
        return {
            'confidence_score': round(confidence_score, 3),
            'recommended_action': action,
            'flags': flags,
            'risk_breakdown': {
                'amount_risk': amount_risk,
                'time_risk': time_risk,
                'location_risk': location_risk,
                'frequency_risk': frequency_risk,
                'merchant_risk': merchant_risk
            }
        }
    
    def _analyze_amount(self, transaction):
        amount = transaction.get('amount', 0)
        
        # Get user's transaction history
        user_id = transaction.get('user_id')
        if user_id:
            recent_transactions = list(self.transactions_collection.find({
                'user_id': user_id,
                'timestamp': {'$gte': datetime.utcnow() - timedelta(days=30)}
            }))
            
            if recent_transactions:
                amounts = [t.get('amount', 0) for t in recent_transactions]
                avg_amount = np.mean(amounts)
                std_amount = np.std(amounts) if len(amounts) > 1 else avg_amount * 0.5
                
                # Z-score based risk
                if std_amount > 0:
                    z_score = abs(amount - avg_amount) / std_amount
                    return min(z_score / 3.0, 1.0)  # Normalize to 0-1
        
        # Default risk based on absolute amount
        if amount > 5000:
            return 0.9
        elif amount > 2000:
            return 0.6
        elif amount > 1000:
            return 0.3
        return 0.1
    
    def _analyze_time(self, transaction):
        hour = transaction.get('hour', datetime.utcnow().hour)
        
        # Higher risk for transactions between 11 PM and 5 AM
        if hour >= 23 or hour <= 5:
            return 0.8
        elif hour >= 21 or hour <= 7:
            return 0.4
        return 0.1
    
    def _analyze_location(self, transaction):
        location = transaction.get('location', {})
        user_id = transaction.get('user_id')
        
        if not location or not user_id:
            return 0.5
        
        # Check if this is a new location for the user
        recent_locations = list(self.transactions_collection.find({
            'user_id': user_id,
            'timestamp': {'$gte': datetime.utcnow() - timedelta(days=90)}
        }))
        
        if not recent_locations:
            return 0.7  # New user, moderate risk
        
        # Check if current location has been used before
        for txn in recent_locations:
            txn_location = txn.get('location', {})
            if (txn_location.get('country') == location.get('country') and
                txn_location.get('city') == location.get('city')):
                return 0.1  # Familiar location
        
        return 0.8  # New location
    
    def _analyze_frequency(self, transaction):
        user_id = transaction.get('user_id')
        if not user_id:
            return 0.3
        
        # Count transactions in the last hour
        recent_count = self.transactions_collection.count_documents({
            'user_id': user_id,
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=1)}
        })
        
        if recent_count >= 5:
            return 1.0
        elif recent_count >= 3:
            return 0.7
        elif recent_count >= 2:
            return 0.4
        return 0.1
    
    def _analyze_merchant(self, transaction):
        merchant = transaction.get('merchant', '').lower()
        
        # List of known safe merchants
        safe_merchants = ['amazon', 'walmart', 'target', 'best buy', 'apple', 'google']
        
        if any(safe in merchant for safe in safe_merchants):
            return 0.1
        elif merchant == 'unknown merchant' or not merchant:
            return 0.9
        else:
            return 0.5
