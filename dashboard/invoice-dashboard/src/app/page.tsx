"use client";
import React, { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [file, setFile] = useState(null);
  const [token, setToken] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file || !token) {
      alert('Please provide both file and token');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await axios.post(
        'http://127.0.0.1:8000/upload-invoice/',
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResults(response.data.classification);
      setMessage(response.data.message);
    } catch (error) {
      console.error(error);
      alert('Upload failed or unauthorized. Check token or server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">
        Invoice Fraud Detection Dashboard
      </h1>

      <input
        type="text"
        placeholder="Enter JWT Token"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        className="mb-4 p-2 border border-gray-300 rounded w-full max-w-md text-gray-800"
      />

      <input
        type="file"
        onChange={handleFileChange}
        className="mb-4 text-gray-800"
      />

      <button
        onClick={handleUpload}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        disabled={loading}
      >
        {loading ? 'Uploading...' : 'Upload Invoice CSV'}
      </button>

      {message && <p className="mt-4 text-green-600">{message}</p>}

      {results.length > 0 && (
        <div className="mt-6 w-full max-w-2xl">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">
            Classification Results
          </h2>
          <table className="table-auto w-full border border-gray-300 text-gray-800">
            <thead>
              <tr className="bg-gray-200">
                <th className="border px-4 py-2">Invoice #</th>
                <th className="border px-4 py-2">Classification</th>
              </tr>
            </thead>
            <tbody>
              {results.map((res, index) => (
                <tr key={index} className="text-center">
                  <td className="border px-4 py-2">{index + 1}</td>
                  <td
                    className={`border px-4 py-2 font-bold ${
                      res === 'Fraudulent'
                        ? 'text-red-600'
                        : 'text-green-600'
                    }`}
                  >
                    {res}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
