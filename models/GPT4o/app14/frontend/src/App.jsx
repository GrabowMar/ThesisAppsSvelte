import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [quota, setQuota] = useState({ used: 0, quota: 0 });
  const [selectedFile, setSelectedFile] = useState(null);

  // Fetch file list and quota on mount
  useEffect(() => {
    fetchFiles();
    fetchQuota();
  }, []);

  const fetchFiles = async () => {
    const response = await fetch('/api/files');
    const data = await response.json();
    setFiles(data.files);
  };

  const fetchQuota = async () => {
    const response = await fetch('/api/quota');
    const data = await response.json();
    setQuota(data);
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return alert("No file selected!");

    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      alert(data.message);
      fetchFiles();
      fetchQuota();
    } else {
      alert(data.error);
    }
  };

  const handleFileDelete = async (filename) => {
    const response = await fetch(`/api/delete/${filename}`, { method: 'DELETE' });
    const data = await response.json();
    if (response.ok) {
      alert(data.message);
      fetchFiles();
      fetchQuota();
    } else {
      alert(data.error);
    }
  };

  const handleFileDownload = (filename) => {
    const downloadUrl = `/api/download/${filename}`;
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="container">
      <h1>File Storage System</h1>
      <p>Used: {quota.used} bytes / Total: {quota.quota} bytes</p>

      <form onSubmit={handleFileUpload}>
        <input
          type="file"
          onChange={(e) => setSelectedFile(e.target.files[0])}
        />
        <button type="submit">Upload File</button>
      </form>

      <h2>Uploaded Files</h2>
      <ul>
        {files.map((file, idx) => (
          <li key={idx}>
            {file}
            <button onClick={() => handleFileDownload(file)}>Download</button>
            <button onClick={() => handleFileDelete(file)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
