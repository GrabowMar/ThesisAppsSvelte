import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [storageQuota, setStorageQuota] = useState(0);

  useEffect(() => {
    fetchFiles();
    fetchStorageQuota();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await fetch("http://localhost:5187/files");
      const data = await response.json();
      setFiles(data.files);
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  };

  const fetchStorageQuota = async () => {
    // Simulated storage quota calculation
    setStorageQuota(50); // Example: 50% used
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5187/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        alert("File uploaded successfully!");
        fetchFiles();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  const handleDownload = async (filename) => {
    window.open(`http://localhost:5187/download/${filename}`, "_blank");
  };

  const handleShare = async (filename) => {
    try {
      const response = await fetch(`http://localhost:5187/share/${filename}`, {
        method: "POST",
      });
      const data = await response.json();
      if (response.ok) {
        alert("File shared successfully!");
        fetchFiles();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error("Error sharing file:", error);
    }
  };

  return (
    <div className="app">
      <h1>File Storage System</h1>
      <div className="quota">
        <div
          className="quota-bar"
          style={{ width: `${storageQuota}%` }}
        ></div>
        <span>{storageQuota}% Used</span>
      </div>
      <input type="file" onChange={handleFileUpload} />
      <h2>Files</h2>
      <ul>
        {files.map((file, index) => (
          <li key={index}>
            <span>{file}</span>
            <button onClick={() => handleDownload(file)}>Download</button>
            <button onClick={() => handleShare(file)}>Share</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
