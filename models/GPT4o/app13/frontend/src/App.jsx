import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [images, setImages] = useState([]);
  const [file, setFile] = useState(null);
  const [viewMode, setViewMode] = useState("grid"); // toggle between grid & list view

  // Fetch images from the API
  const fetchImages = async () => {
    try {
      const response = await fetch("http://localhost:5265/api/images");
      if (!response.ok) {
        throw new Error("Error fetching images.");
      }
      const data = await response.json();
      setImages(data);
    } catch (error) {
      console.error(error.message);
    }
  };

  // Handle file upload
  const handleFileUpload = async () => {
    if (!file) return alert("Please select a file.");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5265/api/images", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (response.ok) {
        alert("Image uploaded successfully.");
        fetchImages();
      } else {
        alert(result.error || "Failed to upload image.");
      }
    } catch (error) {
      console.error(error.message);
    }
  };

  // Lifecycle: Load images on mount
  useEffect(() => {
    fetchImages();
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Gallery Application</h1>
        <div className="upload-section">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button onClick={handleFileUpload}>Upload</button>
        </div>
        <div>
          <button onClick={() => setViewMode("grid")}>Grid View</button>
          <button onClick={() => setViewMode("list")}>List View</button>
        </div>
      </header>
      <main className={viewMode}>
        {images.map((image) => (
          <div className="image-container" key={image.name}>
            <img src={image.url} alt={image.name} />
            <p>{image.name}</p>
          </div>
        ))}
      </main>
    </div>
  );
};

// Mount the React app
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
