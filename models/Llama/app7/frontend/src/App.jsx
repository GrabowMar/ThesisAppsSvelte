import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    axios.get('/api/files')
      .then(response => {
        setFiles(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = () => {
    const formData = new FormData();
    formData.append('file', selectedFile);
    axios.post('/api/upload', formData)
      .then(response => {
        setFiles([...files, { file_id: response.data.file_id, filename: selectedFile.name }]);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleDownload = (fileId) => {
    axios.get(`/api/download/${fileId}`, { responseType: 'blob' })
      .then(response => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const a = document.createElement('a');
        a.href = url;
        a.download = files.find(file => file.file_id === fileId).filename;
        a.click();
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handlePreview = (fileId) => {
    axios.get(`/api/preview/${fileId}`)
      .then(response => {
        setPreview(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <h1>File Uploader</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <ul>
        {files.map((file) => (
          <li key={file.file_id}>
            {file.filename}
            <button onClick={() => handleDownload(file.file_id)}>Download</button>
            <button onClick={() => handlePreview(file.file_id)}>Preview</button>
          </li>
        ))}
      </ul>
      {preview && (
        <div>
          <h2>Preview</h2>
          <p>{preview.filename}</p>
          <pre>{preview.content}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
