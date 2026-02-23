from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import json
import math
import numpy as np

@dataclass
class Location:
    """Geographic location information for a transaction"""
    country: str
    city: str
    lat: float
    lng: float
    region: Optional[str] = None
    postal_code: Optional[str] = None
    ip_address: Optional[str] = None
   
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        return cls(**data)
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance in kilometers using Haversine formula"""
       
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [self.lat, self.lng, other.lat, other.lng])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r

@dataclass
class FraudAnalysis:
    """Results of fraud detection analysis"""
    confidence_score: float
    risk_score: float
    recommended_action: str  # 'approve', 'flag', 'block'
    flags: List[str]
    risk_breakdown: Dict[str, float]
    analysis_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FraudAnalysis':
        if isinstance(data['analysis_timestamp'], str):
            data['analysis_timestamp'] = datetime.fromisoformat(data['analysis_timestamp'])
        return cls(**data)

@dataclass
class Transaction:
    """Main transaction model with all relevant information"""
    transaction_id: str
    user_id: str
    amount: float
    merchant: str
    location: Location
    timestamp: datetime
    payment_method: str
    hour: Optional[int] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    card_last_four: Optional[str] = None
    currency: str = 'USD'
    category: Optional[str] = None
    description: Optional[str] = None
    fraud_analysis: Optional[FraudAnalysis] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.hour is None:
            self.hour = self.timestamp.hour
        
        # Ensure location is Location object
        if isinstance(self.location, dict):
            self.location = Location.from_dict(self.location)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        if self.fraud_analysis:
            result['fraud_analysis'] = self.fraud_analysis.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary"""
        # Handle timestamp conversion
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Handle location conversion
        if isinstance(data['location'], dict):
            data['location'] = Location.from_dict(data['location'])
        
        # Handle fraud analysis conversion
        if data.get('fraud_analysis') and isinstance(data['fraud_analysis'], dict):
            data['fraud_analysis'] = FraudAnalysis.from_dict(data['fraud_analysis'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert transaction to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Transaction':
        """Create transaction from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_high_risk(self) -> bool:
        """Check if transaction is high risk based on fraud analysis"""
        if not self.fraud_analysis:
            return False
        return (self.fraud_analysis.confidence_score >= 0.7 or 
                self.fraud_analysis.risk_score >= 0.7)
    
    def is_blocked(self) -> bool:
        """Check if transaction should be blocked"""
        if not self.fraud_analysis:
            return False
        return self.fraud_analysis.recommended_action == 'block'
    
    def is_flagged(self) -> bool:
        """Check if transaction should be flagged for review"""
        if not self.fraud_analysis:
            return False
        return self.fraud_analysis.recommended_action in ['flag', 'block']
    
    def get_risk_level(self) -> str:
        """Get human-readable risk level"""
        if not self.fraud_analysis:
            return 'Unknown'
        
        risk_score = max(self.fraud_analysis.confidence_score, self.fraud_analysis.risk_score)
        
        if risk_score >= 0.8:
            return 'Critical'
        elif risk_score >= 0.6:
            return 'High'
        elif risk_score >= 0.4:
            return 'Medium'
        elif risk_score >= 0.2:
            return 'Low-Medium'
        else:
            return 'Low'
    
    def add_fraud_analysis(self, analysis: FraudAnalysis) -> None:
        """Add fraud analysis results to transaction"""
        self.fraud_analysis = analysis
    
    def get_suspicious_indicators(self) -> List[str]:
        """Get list of suspicious indicators for this transaction"""
        indicators = []
        
        # High amount indicator
        if self.amount > 5000:
            indicators.append(f"High amount: ${self.amount:,.2f}")
        
        # Unusual time indicator
        if self.hour is not None and (self.hour <= 5 or self.hour >= 23):
            indicators.append(f"Unusual time: {self.hour}:00")
        
        # Unknown merchant
        if self.merchant.lower() in ['unknown merchant', 'unknown', '']:
            indicators.append("Unknown merchant")
        
        # Add fraud analysis flags if available
        if self.fraud_analysis and self.fraud_analysis.flags:
            indicators.extend(self.fraud_analysis.flags)
        
        return indicators
    
    def validate(self) -> List[str]:
        """Validate transaction data and return list of validation errors"""
        errors = []
        
        if not self.transaction_id:
            errors.append("Transaction ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if self.amount <= 0:
            errors.append("Amount must be positive")
        
        if not self.merchant:
            errors.append("Merchant is required")
        
        if not isinstance(self.location, Location):
            errors.append("Valid location is required")
        
        if not self.payment_method:
            errors.append("Payment method is required")
        
        # Validate location
        if isinstance(self.location, Location):
            if not (-90 <= self.location.lat <= 90):
                errors.append("Invalid latitude")
            if not (-180 <= self.location.lng <= 180):
                errors.append("Invalid longitude")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if transaction data is valid"""
        return len(self.validate()) == 0

class TransactionRepository:
    """Repository class for transaction database operations"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.transactions
    
    def save(self, transaction: Transaction) -> str:
        """Save transaction to database"""
        if not transaction.is_valid():
            raise ValueError(f"Invalid transaction data: {transaction.validate()}")
        
        transaction_dict = transaction.to_dict()
        result = self.collection.insert_one(transaction_dict)
        return str(result.inserted_id)
    
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Find transaction by ID"""
        data = self.collection.find_one({'transaction_id': transaction_id})
        if data:
            # Remove MongoDB _id field
            data.pop('_id', None)
            return Transaction.from_dict(data)
        return None
    
    def find_by_user(self, user_id: str, limit: int = 100) -> List[Transaction]:
        """Find transactions by user ID"""
        cursor = self.collection.find({'user_id': user_id}).sort('timestamp', -1).limit(limit)
        transactions = []
        for data in cursor:
            data.pop('_id', None)
            transactions.append(Transaction.from_dict(data))
        return transactions
    
    def find_recent(self, hours: int = 24, limit: int = 100) -> List[Transaction]:
        """Find recent transactions"""
        cutoff_time = datetime.utcnow() - datetime.timedelta(hours=hours)
        cursor = self.collection.find({
            'timestamp': {'$gte': cutoff_time}
        }).sort('timestamp', -1).limit(limit)
        
        transactions = []
        for data in cursor:
            data.pop('_id', None)
            transactions.append(Transaction.from_dict(data))
        return transactions
    
    def find_high_risk(self, limit: int = 50) -> List[Transaction]:
        """Find high-risk transactions"""
        cursor = self.collection.find({
            '$or': [
                {'fraud_analysis.confidence_score': {'$gte': 0.7}},
                {'fraud_analysis.risk_score': {'$gte': 0.7}},
                {'fraud_analysis.recommended_action': {'$in': ['flag', 'block']}}
            ]
        }).sort('timestamp', -1).limit(limit)
        
        transactions = []
        for data in cursor:
            data.pop('_id', None)
            transactions.append(Transaction.from_dict(data))
        return transactions
    
    def get_fraud_statistics(self) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        total_transactions = self.collection.count_documents({})
        flagged_transactions = self.collection.count_documents({
            'fraud_analysis.recommended_action': 'flag'
        })
        blocked_transactions = self.collection.count_documents({
            'fraud_analysis.recommended_action': 'block'
        })
        
        fraud_rate = 0
        if total_transactions > 0:
            fraud_rate = ((flagged_transactions + blocked_transactions) / total_transactions) * 100
        
        return {
            'total_transactions': total_transactions,
            'flagged_transactions': flagged_transactions,
            'blocked_transactions': blocked_transactions,
            'approved_transactions': total_transactions - flagged_transactions - blocked_transactions,
            'fraud_rate': round(fraud_rate, 2)
        }
    
    def update_fraud_analysis(self, transaction_id: str, analysis: FraudAnalysis) -> bool:
        """Update fraud analysis for a transaction"""
        result = self.collection.update_one(
            {'transaction_id': transaction_id},
            {'$set': {'fraud_analysis': analysis.to_dict()}}
        )
        return result.modified_count > 0

# Example usage and utility functions
def create_sample_transaction() -> Transaction:
    """Create a sample transaction for testing"""
    return Transaction(
        transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        user_id="USER_1001",
        amount=150.00,
        merchant="Amazon",
        location=Location(
            country="USA",
            city="New York",
            lat=40.7128,
            lng=-74.0060
        ),
        timestamp=datetime.utcnow(),
        payment_method="credit_card",
        currency="USD",
        category="online_shopping"
    )

def create_suspicious_transaction() -> Transaction:
    """Create a suspicious transaction for testing"""
    return Transaction(
        transaction_id=f"FRAUD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        user_id="USER_9999",
        amount=5000.00,
        merchant="Unknown Merchant",
        location=Location(
            country="Unknown",
            city="Unknown",
            lat=0.0,
            lng=0.0
        ),
        timestamp=datetime.utcnow(),
        payment_method="credit_card",
        hour=3,  # 3 AM
        currency="USD",
        category="unknown"
    )
