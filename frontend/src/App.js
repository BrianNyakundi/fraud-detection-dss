import React from 'react';
import './App.css';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <h1>🛡️ Fraud Detection & Prevention System</h1>
        <div className="header-status">
          <span className="status-indicator active"></span>
          <span>System Active</span>
        </div>
      </header>
      
      <main className="app-main">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
