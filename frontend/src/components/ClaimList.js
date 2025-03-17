// src/components/ClaimList.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ClaimList = () => {
  const [claims, setClaims] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/claims')  // Replace with your FastAPI endpoint
      .then(response => {
        setClaims(response.data);
      })
      .catch(error => {
        console.error('Error fetching claims:', error);
      });
  }, []);

  return (
    <div>
      <h1>Processed Claims</h1>
      <table>
        <thead>
          <tr>
            <th>Claim ID</th>
            <th>Patient Name</th>
            <th>Amount</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {claims.map(claim => (
            <tr key={claim.id}>
              <td>{claim.id}</td>
              <td>{claim.patient_name}</td>
              <td>{claim.amount}</td>
              <td>{claim.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ClaimList;

