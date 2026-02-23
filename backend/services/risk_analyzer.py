import math
from datetime import datetime, timedelta

class RiskAnalyzer:
    def __init__(self, db):
        self.db = db
        self.transactions_collection = db['transactions']
    
    def calculate_risk_score(self, transaction):
        risk_components = []
        
        # Velocity risk (transaction frequency)
        velocity_risk = self._calculate_velocity_risk(transaction)
        risk_components.append(velocity_risk * 0.25)
        
        # Geographic risk
        geo_risk = self._calculate_geographic_risk(transaction)
        risk_components.append(geo_risk * 0.2)
        
        # Amount deviation risk
        amount_risk = self._calculate_amount_deviation_risk(transaction)
        risk_components.append(amount_risk * 0.3)
        
        # Time pattern risk
        time_risk = self._calculate_time_pattern_risk(transaction)
        risk_components.append(time_risk * 0.15)
        
        # Device/method risk
        device_risk = self._calculate_device_risk(transaction)
        risk_components.append(device_risk * 0.1)
        
        return min(sum(risk_components), 1.0)
    
    def _calculate_velocity_risk(self, transaction):
        user_id = transaction.get('user_id')
        if not user_id:
            return 0.5
        
        # Count transactions in various time windows
        now = datetime.utcnow()
        
        count_1h = self.transactions_collection.count_documents({
            'user_id': user_id,
            'timestamp': {'$gte': now - timedelta(hours=1)}
        })
        
        count_24h = self.transactions_collection.count_documents({
            'user_id': user_id,
            'timestamp': {'$gte': now - timedelta(hours=24)}
        })
        
        # Risk based on velocity
        if count_1h >= 10:
            return 1.0
        elif count_1h >= 5:
            return 0.8
        elif count_24h >= 50:
            return 0.7
        elif count_24h >= 20:
            return 0.4
        else:
            return 0.1
    
    def _calculate_geographic_risk(self, transaction):
        location = transaction.get('location', {})
        country = location.get('country', '').lower()
        
        # High-risk countries (simplified list)
        high_risk_countries = ['unknown', 'tor', 'proxy']
        medium_risk_countries = ['nigeria', 'russia', 'china', 'iran', 'north korea']
        
        if any(risk in country for risk in high_risk_countries):
            return 1.0
        elif any(risk in country for risk in medium_risk_countries):
            return 0.6
        else:
            return 0.2
    
    def _calculate_amount_deviation_risk(self, transaction):
        amount = transaction.get('amount', 0)
        user_id = transaction.get('user_id')
        
        if not user_id:
            return 0.3
        
        # Get historical transaction amounts
        historical = list(self.transactions_collection.find({
            'user_id': user_id,
            'timestamp': {'$gte': datetime.utcnow() - timedelta(days=60)}
        }))
        
        if len(historical) < 3:
            return 0.4  # Limited history
        
        amounts = [t.get('amount', 0) for t in historical]
        avg_amount = sum(amounts) / len(amounts)
        
        # Calculate standard deviation
        variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.8 if amount != avg_amount else 0.1
        
        # Z-score calculation
        z_score = abs(amount - avg_amount) / std_dev
        
        if z_score > 3:
            return 1.0
        elif z_score > 2:
            return 0.7
        elif z_score > 1:
            return 0.3
        else:
            return 0.1
    
    def _calculate_time_pattern_risk(self, transaction):
        hour = transaction.get('hour', datetime.utcnow().hour)
        user_id = transaction.get('user_id')
        
        # Base risk by hour
        if 2 <= hour <= 5:  # Very unusual hours
            base_risk = 0.9
        elif 22 <= hour <= 23 or 6 <= hour <= 7:  # Somewhat unusual
            base_risk = 0.4
        else:
            base_risk = 0.1
        
        if not user_id:
            return base_risk
        
        # Check user's historical patterns
        historical = list(self.transactions_collection.find({
            'user_id': user_id,
            'timestamp': {'$gte': datetime.utcnow() - timedelta(days=30)}
        }))
        
        if len(historical) < 5:
            return base_risk
        
        # Check if this hour is common for this user
        user_hours = [t.get('hour', datetime.utcfromtimestamp(t['timestamp'].timestamp()).hour) 
                      for t in historical]
        
        hour_frequency = user_hours.count(hour) / len(user_hours)
        
        if hour_frequency > 0.1:  # User commonly transacts at this hour
            return 0.1
        elif hour_frequency > 0.05:
            return 0.3
        else:
            return base_risk
    
    def _calculate_device_risk(self, transaction):
        payment_method = transaction.get('payment_method', '').lower()
        
        # Risk by payment method
        method_risks = {
            'credit_card': 0.1,
            'debit_card': 0.2,
            'digital_wallet': 0.15,
            'cryptocurrency': 0.8,
            'wire_transfer': 0.6,
            'unknown': 0.9
        }
        
        return method_risks.get(payment_method, 0.5)
