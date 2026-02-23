import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import apiService from '../services/api';

// Custom hook for heat map layer
const HeatMapLayer = ({ heatMapData }) => {
  const map = useMap();
  const [heatLayer, setHeatLayer] = useState(null);

  useEffect(() => {
    if (!heatMapData || heatMapData.length === 0) return;

    // Remove existing heat layer
    if (heatLayer) {
      map.removeLayer(heatLayer);
    }

    // Prepare heat map points
    const heatPoints = heatMapData.map(point => [
      point._id.lat,
      point._id.lng,
      Math.min(point.avg_risk_score || 0.5, 1.0) // Intensity based on risk score
    ]).filter(point => 
      !isNaN(point[0]) && !isNaN(point[1]) && point[0] !== null && point[1] !== null
    );

    if (heatPoints.length === 0) return;

    // Create heat layer using canvas overlay
    const newHeatLayer = L.featureGroup();

    // Create circle markers for heat visualization
    heatPoints.forEach(([lat, lng, intensity]) => {
      const color = getHeatColor(intensity);
      const radius = Math.max(intensity * 50, 10); // Scale radius by intensity

      const circle = L.circleMarker([lat, lng], {
        radius: radius,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: 0.6,
        fillOpacity: 0.4
      });

      // Add popup with details
      const pointData = heatMapData.find(p => 
        p._id.lat === lat && p._id.lng === lng
      );
      
      if (pointData) {
        circle.bindPopup(`
          <div style="min-inline-size: 180px;">
            <h4 style="margin: 0 0 8px 0; color: #333;">🔥 Fraud Hotspot</h4>
            <p style="margin: 4px 0;"><strong>Location:</strong> ${pointData._id.city}, ${pointData._id.country}</p>
            <p style="margin: 4px 0;"><strong>Fraud Attempts:</strong> ${pointData.fraud_count}</p>
            <p style="margin: 4px 0;"><strong>Avg Risk Score:</strong> ${(pointData.avg_risk_score * 100).toFixed(1)}%</p>
            <p style="margin: 4px 0;"><strong>Threat Level:</strong> ${getThreatLevel(pointData.avg_risk_score)}</p>
          </div>
        `);
      }

      newHeatLayer.addLayer(circle);
    });

    newHeatLayer.addTo(map);
    setHeatLayer(newHeatLayer);

    return () => {
      if (newHeatLayer) {
        map.removeLayer(newHeatLayer);
      }
    };
  }, [heatMapData, map]);

  return null;
};

// Helper function to get heat color based on intensity
const getHeatColor = (intensity) => {
  if (intensity >= 0.8) return '#FF0000'; // Red - Very High Risk
  if (intensity >= 0.6) return '#FF4500'; // Orange Red - High Risk
  if (intensity >= 0.4) return '#FF8C00'; // Dark Orange - Medium Risk
  if (intensity >= 0.2) return '#FFD700'; // Gold - Low-Medium Risk
  return '#FFFF00'; // Yellow - Low Risk
};

// Helper function to get threat level description
const getThreatLevel = (riskScore) => {
  if (riskScore >= 0.8) return '🚨 Critical';
  if (riskScore >= 0.6) return '⚠️ High';
  if (riskScore >= 0.4) return '⚡ Medium';
  if (riskScore >= 0.2) return '🟡 Low-Medium';
  return '🟢 Low';
};

const HeatMap = ({ className = '' }) => {
  const [heatMapData, setHeatMapData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadHeatMapData();
    
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(loadHeatMapData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadHeatMapData = async () => {
    try {
      setError(null);
      const data = await apiService.getHeatMapData();
      setHeatMapData(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to load heat map data');
      console.error('Heat map data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getHeatMapStats = () => {
    if (!heatMapData.length) return { totalHotspots: 0, highestRisk: 0, totalThreats: 0 };
    
    return {
      totalHotspots: heatMapData.length,
      highestRisk: Math.max(...heatMapData.map(d => d.avg_risk_score)) * 100,
      totalThreats: heatMapData.reduce((sum, d) => sum + d.fraud_count, 0)
    };
  };

  const stats = getHeatMapStats();

  if (loading) {
    return (
      <div className={`heat-map-container ${className}`}>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading heat map data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`heat-map-container ${className}`}>
        <div className="error-message">
          <p>⚠️ {error}</p>
          <button onClick={loadHeatMapData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`heat-map-container ${className}`}>
      {/* Heat Map Stats Header */}
      <div className="heat-map-header">
        <div className="heat-map-stats">
          <div className="stat-item">
            <span className="stat-label">Hotspots:</span>
            <span className="stat-value">{stats.totalHotspots}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Highest Risk:</span>
            <span className="stat-value">{stats.highestRisk.toFixed(1)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Threats:</span>
            <span className="stat-value">{stats.totalThreats}</span>
          </div>
        </div>
        <div className="last-update">
          Last updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
        </div>
      </div>

      {/* Map Container */}
      <div className="map-wrapper">
        <MapContainer 
          center={[40.7128, -74.0060]} 
          zoom={2} 
          style={{ blockSize: '400px', inlineSize: '100%' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <HeatMapLayer heatMapData={heatMapData} />
        </MapContainer>

        {/* Heat Map Legend */}
        <div className="heat-map-legend">
          <h4>Risk Intensity</h4>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#FFFF00' }}></div>
              <span>Low (0-20%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#FFD700' }}></div>
              <span>Low-Med (20-40%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#FF8C00' }}></div>
              <span>Medium (40-60%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#FF4500' }}></div>
              <span>High (60-80%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#FF0000' }}></div>
              <span>Critical (80%+)</span>
            </div>
          </div>
        </div>
      </div>

      {/* No Data Message */}
      {heatMapData.length === 0 && (
        <div className="no-data-message">
          <p>🗺️ No fraud hotspots detected in the last 24 hours</p>
        </div>
      )}
    </div>
  );
};

export default HeatMap;