import React from 'react';

const AlertPanel = ({ alerts, onClearAlert }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'block': return '🚫';
      case 'flag': return '⚠️';
      default: return '🔔';
    }
  };

  if (alerts.length === 0) return null;

  return (
    <div className="alert-panel">
      <div className="alert-header">
        🚨 Real-Time Alerts ({alerts.length})
      </div>
      <div className="alert-list">
        {alerts.map((alert) => (
          <div key={alert.id} className="alert-item">
            <div className="alert-time">
              {formatTime(alert.timestamp)}
            </div>
            <p className="alert-message">
              {getAlertIcon(alert.type)} {alert.message}
            </p>
            <button
              onClick={() => onClearAlert(alert.id)}
              style={{
                position: 'absolute',
                insetBlockStart: '8px',
                insetInlineEnd: '8px',
                background: 'none',
                border: 'none',
                fontSize: '1.2rem',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertPanel;
