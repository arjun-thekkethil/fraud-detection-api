import React from 'react';
import './App.css';
import ClaimList from './components/ClaimList';  // Make sure to import the ClaimList component

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Medical Claims Dashboard</h1>
        <ClaimList />  {/* Render the ClaimList component */}
      </header>
    </div>
  );
}

export default App;
