import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const TransactionMap = ({ transactions }) => {
  const [mapCenter] = useState([40.7128, -74.0060]); // Default to NYC
  const [mapZoom] = useState(2);

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.8) return '#F44336'; // Red - High Risk
    if (riskScore >= 0.5) return '#FF9800'; // Orange - Medium Risk
    if (riskScore >= 0.3) return '#FFC107'; // Yellow - Low-Medium Risk
    return '#4CAF50'; // Green - Low Risk
  };

  const getRiskRadius = (riskScore, amount) => {
    const baseRadius = Math.log(amount + 1) * 2; // Logarithmic scale for amount
    const riskMultiplier = riskScore * 2 + 1; // Risk multiplier (1-3x)
    return Math.min(Math.max(baseRadius * riskMultiplier, 5), 50); // Clamp between 5-50
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'block': return '🚫';
      case 'flag': return '⚠️';
      case 'approve': return '✅';
      default: return '❓';
    }
  };

  // Filter transactions that have location data
  const validTransactions = transactions.filter(t => 
    t.location && 
    typeof t.location.lat === 'number' && 
    typeof t.location.lng === 'number' &&
    !isNaN(t.location.lat) && 
    !isNaN(t.location.lng)
  );

  return (
    <div className="map-container">
      <MapContainer center={mapCenter} zoom={mapZoom} style={{ blocksize: '100%', inlinesize: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {validTransactions.map((transaction, index) => {
          const riskScore = transaction.risk_score || transaction.confidence_score || 0;
          const position = [transaction.location.lat, transaction.location.lng];
          
          return (
            <CircleMarker
              key={`${transaction.transaction_id}-${index}`}
              center={position}
              radius={getRiskRadius(riskScore, transaction.amount || 100)}
              fillColor={getRiskColor(riskScore)}
              color={getRiskColor(riskScore)}
              weight={2}
              opacity={0.8}
              fillOpacity={0.6}
            >
              <Popup>
                <div style={{ mininline-size: '200px' }}>
                  <h4 style={{ margin: '0 0 8px 0', color: '#333' }}>
                    {getActionIcon(transaction.action)} Transaction Details
                  </h4>
                  <p style={{ margin: '4px 0' }}>
                    <strong>ID:</strong> {transaction.transaction_id}
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Amount:</strong> ${transaction.amount?.toLocaleString() || 'N/A'}
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Location:</strong> {transaction.location.city}, {transaction.location.country}
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Risk Score:</strong> {(riskScore * 100).toFixed(1)}%
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Action:</strong> 
                    <span style={{ 
                      color: getRiskColor(riskScore), 
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}>
                      {transaction.action}
                    </span>
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Time:</strong> {new Date(transaction.timestamp).toLocaleString()}
                  </p>
                  {transaction.merchant && (
                    <p style={{ margin: '4px 0' }}>
                      <strong>Merchant:</strong> {transaction.merchant}
                    </p>
                  )}
                  {transaction.flags && transaction.flags.length > 0 && (
                    <div style={{ margininset-block-start: '8px' }}>
                      <strong>Flags:</strong>
                      <ul style={{ margin: '4px 0', paddinginset-inline-start: '16px' }}>
                        {transaction.flags.map((flag, i) => (
                          <li key={i} style={{ fontSize: '0.9em', color: '#F44336' }}>
                            {flag}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      
      {/* Risk Legend */}
      <div className="heat-map-legend">
        <div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem' }}>Risk Level</h4>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#4CAF50' }}></div>
            <span>Low (0-30%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#FFC107' }}></div>
            <span>Medium (30-50%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#FF9800' }}></div>
            <span>High (50-80%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#F44336' }}></div>
            <span>Critical (80%+)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionMap;
