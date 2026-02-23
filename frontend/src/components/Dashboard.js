import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import TransactionMap from './TransactionMap';
import AlertPanel from './AlertPanel';
import apiService from '../services/api';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    recent_transactions: [],
    fraud_stats: {
      total_transactions: 0,
      flagged_transactions: 0,
      blocked_transactions: 0
    }
  });
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Initialize socket connection
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    // Listen for real-time transaction updates
    newSocket.on('transaction_update', (transaction) => {
      // Add to recent transactions
      setDashboardData(prev => ({
        ...prev,
        recent_transactions: [transaction, ...prev.recent_transactions.slice(0, 49)]
      }));

      // Add to alerts if high risk
      if (transaction.action === 'block' || transaction.risk_score > 0.7) {
        const alert = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          message: `${transaction.action.toUpperCase()}: Transaction ${transaction.transaction_id} - $${transaction.amount} - Risk Score: ${(transaction.risk_score * 100).toFixed(1)}%`,
          type: transaction.action,
          transaction_id: transaction.transaction_id
        };
        setAlerts(prev => [alert, ...prev.slice(0, 19)]); // Keep last 20 alerts
      }
    });

    // Load initial data
    loadDashboardData();

    return () => {
      newSocket.close();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateFraudRate = () => {
    const { total_transactions, flagged_transactions, blocked_transactions } = dashboardData.fraud_stats;
    if (total_transactions === 0) return 0;
    return (((flagged_transactions + blocked_transactions) / total_transactions) * 100).toFixed(1);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getStatusColor = (action) => {
    switch (action) {
      case 'approve': return '#4CAF50';
      case 'flag': return '#FF9800';
      case 'block': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Dashboard Header Stats */}
      <div className="dashboard-header">
        <div className="stat-card total">
          <h3>Total Transactions</h3>
          <p className="value">{dashboardData.fraud_stats.total_transactions.toLocaleString()}</p>
        </div>
        <div className="stat-card flagged">
          <h3>Flagged for Review</h3>
          <p className="value">{dashboardData.fraud_stats.flagged_transactions.toLocaleString()}</p>
        </div>
        <div className="stat-card blocked">
          <h3>Blocked Transactions</h3>
          <p className="value">{dashboardData.fraud_stats.blocked_transactions.toLocaleString()}</p>
        </div>
        <div className="stat-card rate">
          <h3>Fraud Rate</h3>
          <p className="value">{calculateFraudRate()}%</p>
        </div>
      </div>

      {/* Main Dashboard Content */}
      <div className="dashboard-content">
        {/* Recent Transactions Panel */}
        <div className="transactions-panel">
          <div className="panel-header">
            <h2 className="panel-title">📊 Recent Transactions</h2>
            <button className="refresh-btn" onClick={loadDashboardData}>
              🔄 Refresh
            </button>
          </div>
          <div className="transaction-list">
            {dashboardData.recent_transactions.map((transaction, index) => (
              <div key={`${transaction.transaction_id}-${index}`} className="transaction-item">
                <div className="transaction-info">
                  <h4>Transaction {transaction.transaction_id}</h4>
                  <p>
                    {transaction.location?.city}, {transaction.location?.country} • 
                    {formatTime(transaction.timestamp)} • 
                    {transaction.merchant || 'Unknown Merchant'}
                  </p>
                  {transaction.flags && transaction.flags.length > 0 && (
                    <p style={{ color: '#F44336', fontSize: '0.7rem' }}>
                      🚩 {transaction.flags.join(', ')}
                    </p>
                  )}
                </div>
                <div className="transaction-status">
                  <div className="transaction-amount">
                    ${transaction.amount?.toLocaleString() || 'N/A'}
                  </div>
                  <span className={`status-badge ${transaction.action}`}>
                    {transaction.action}
                  </span>
                  <div className="confidence-score">
                    Risk: {((transaction.risk_score || transaction.confidence_score || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
            {dashboardData.recent_transactions.length === 0 && (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                No transactions available
              </div>
            )}
          </div>
        </div>

        {/* Transaction Map Panel */}
        <div className="map-panel">
          <div className="panel-header">
            <h2 className="panel-title">🗺️ Transaction Heat Map</h2>
            <div style={{ fontSize: '0.8rem', color: '#666' }}>
              Real-time fraud risk visualization
            </div>
          </div>
          <TransactionMap transactions={dashboardData.recent_transactions} />
        </div>
      </div>

      {/* Alert Panel */}
      {alerts.length > 0 && <AlertPanel alerts={alerts} onClearAlert={(id) => {
        setAlerts(prev => prev.filter(alert => alert.id !== id));
      }} />}
    </div>
  );
};

export default Dashboard;
