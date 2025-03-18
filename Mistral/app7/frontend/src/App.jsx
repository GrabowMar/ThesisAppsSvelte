import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5093/files');
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      await axios.post('http://localhost:5093/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      fetchFiles();
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleFileDownload = async (filename) => {
    try {
      const response = await axios.get(`http://localhost:5093/download/${filename}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  return (
    <Router>
      <div className="App">
        <nav>
          <Link to="/">Upload</Link>
          <Link to="/files">Files</Link>
        </nav>
        <Switch>
          <Route exact path="/">
            <div>
              <h1>Upload File</h1>
              <input type="file" onChange={handleFileChange} />
              <button onClick={handleFileUpload}>Upload</button>
            </div>
          </Route>
          <Route path="/files">
            <div>
              <h1>Files</h1>
              <ul>
                {files.map((file) => (
                  <li key={file}>
                    {file}
                    <button onClick={() => handleFileDownload(file)}>Download</button>
                  </li>
                ))}
              </ul>
            </div>
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
