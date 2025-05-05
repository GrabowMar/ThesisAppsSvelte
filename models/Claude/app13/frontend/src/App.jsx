import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5345/api';

// Main App Component
function App() {
  // State Management
  const [view, setView] = useState('galleries'); // galleries, gallery, imageDetails
  const [galleries, setGalleries] = useState([]);
  const [currentGallery, setCurrentGallery] = useState(null);
  const [galleryImages, setGalleryImages] = useState([]);
  const [currentImage, setCurrentImage] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // grid, list
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // UI State
  const [isNewGalleryModalOpen, setIsNewGalleryModalOpen] = useState(false);
  const [isEditGalleryModalOpen, setIsEditGalleryModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isEditImageModalOpen, setIsEditImageModalOpen] = useState(false);
  
  // Form States
  const [newGalleryName, setNewGalleryName] = useState('');
  const [newGalleryDesc, setNewGalleryDesc] = useState('');
  const [editGalleryName, setEditGalleryName] = useState('');
  const [editGalleryDesc, setEditGalleryDesc] = useState('');
  const [imageTitle, setImageTitle] = useState('');
  const [imageDesc, setImageDesc] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // API Calls
  const fetchGalleries = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/galleries`);
      if (!response.ok) throw new Error('Failed to fetch galleries');
      const data = await response.json();
      setGalleries(data);
    } catch (err) {
      setError('Error loading galleries: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchGalleryDetails = useCallback(async (galleryId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/galleries/${galleryId}`);
      if (!response.ok) throw new Error('Failed to fetch gallery details');
      const data = await response.json();
      setCurrentGallery(data.gallery);
      setGalleryImages(data.images);
    } catch (err) {
      setError('Error loading gallery: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchImageDetails = useCallback(async (imageId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/images/${imageId}`);
      if (!response.ok) throw new Error('Failed to fetch image details');
      const data = await response.json();
      setCurrentImage(data);
      setImageTitle(data.title);
      setImageDesc(data.description);
    } catch (err) {
      setError('Error loading image: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createGallery = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/galleries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newGalleryName,
          description: newGalleryDesc,
        }),
      });
      if (!response.ok) throw new Error('Failed to create gallery');
      await fetchGalleries();
      setIsNewGalleryModalOpen(false);
      setNewGalleryName('');
      setNewGalleryDesc('');
    } catch (err) {
      setError('Error creating gallery: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const updateGallery = async () => {
    if (!currentGallery) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/galleries/${currentGallery.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editGalleryName,
          description: editGalleryDesc,
        }),
      });
      if (!response.ok) throw new Error('Failed to update gallery');
      
      // Update the current gallery in state
      setCurrentGallery(prev => ({
        ...prev,
        name: editGalleryName,
        description: editGalleryDesc,
      }));
      
      // Update galleries list
      await fetchGalleries();
      setIsEditGalleryModalOpen(false);
    } catch (err) {
      setError('Error updating gallery: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteGallery = async (galleryId) => {
    if (window.confirm('Are you sure you want to delete this gallery? Images will be moved to the default gallery.')) {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/galleries/${galleryId}`, {
          method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to delete gallery');
        await fetchGalleries();
        setView('galleries');
      } catch (err) {
        setError('Error deleting gallery: ' + err.message);
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const uploadImage = async (event) => {
    event.preventDefault();
    if (!selectedFile || !currentGallery) return;
    
    setIsLoading(true);
    setUploadProgress(0);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('gallery_id', currentGallery.id);
      formData.append('title', imageTitle);
      formData.append('description', imageDesc);
      
      const xhr = new XMLHttpRequest();
      
      xhr.open('POST', `${API_BASE_URL}/images`, true);
      
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          fetchGalleryDetails(currentGallery.id);
          setIsUploadModalOpen(false);
          setSelectedFile(null);
          setImageTitle('');
          setImageDesc('');
          setUploadProgress(0);
        } else {
          throw new Error('Upload failed with status: ' + xhr.status);
        }
        setIsLoading(false);
      };
      
      xhr.onerror = () => {
        setError('Upload failed. Please try again.');
        setIsLoading(false);
      };
      
      xhr.send(formData);
      
    } catch (err) {
      setError('Error uploading image: ' + err.message);
      console.error(err);
      setIsLoading(false);
    }
  };

  const updateImage = async () => {
    if (!currentImage) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/images/${currentImage.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: imageTitle,
          description: imageDesc,
        }),
      });
      if (!response.ok) throw new Error('Failed to update image');
      
      // Update current image state
      setCurrentImage(prev => ({
        ...prev,
        title: imageTitle,
        description: imageDesc,
      }));
      
      // Update in gallery images list
      setGalleryImages(prev => 
        prev.map(img => 
          img.id === currentImage.id 
            ? { ...img, title: imageTitle, description: imageDesc }
            : img
        )
      );
      
      setIsEditImageModalOpen(false);
    } catch (err) {
      setError('Error updating image: ' + err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteImage = async (imageId) => {
    if (window.confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/images/${imageId}`, {
          method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to delete image');
        
        if (view === 'imageDetails') {
          setView('gallery');
        }
        
        if (currentGallery) {
          fetchGalleryDetails(currentGallery.id);
        }
      } catch (err) {
        setError('Error deleting image: ' + err.message);
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Lifecycle Hooks
  useEffect(() => {
    fetchGalleries();
  }, [fetchGalleries]);

  // Event Handlers
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const openGallery = (gallery) => {
    fetchGalleryDetails(gallery.id);
    setView('gallery');
  };

  const openImageDetails = (image) => {
    fetchImageDetails(image.id);
    setView('imageDetails');
  };

  const openEditGalleryModal = () => {
    setEditGalleryName(currentGallery.name);
    setEditGalleryDesc(currentGallery.description);
    setIsEditGalleryModalOpen(true);
  };

  const openEditImageModal = () => {
    setImageTitle(currentImage.title);
    setImageDesc(currentImage.description);
    setIsEditImageModalOpen(true);
  };

  // UI Components
  const Navigation = () => (
    <nav className="app-navigation">
      <div className="app-title">
        <h1>Gallery App</h1>
      </div>
      <div className="app-breadcrumbs">
        <button onClick={() => setView('galleries')}>Galleries</button>
        {currentGallery && view !== 'galleries' && (
          <>
            <span>/</span>
            <button onClick={() => setView('gallery')}>{currentGallery.name}</button>
          </>
        )}
        {view === 'imageDetails' && currentImage && (
          <>
            <span>/</span>
            <span>{currentImage.title || 'Image Details'}</span>
          </>
        )}
      </div>
    </nav>
  );

  const GalleriesView = () => (
    <div className="galleries-view">
      <div className="gallery-header">
        <h2>Your Galleries</h2>
        <button 
          className="primary-button" 
          onClick={() => setIsNewGalleryModalOpen(true)}
        >
          Create Gallery
        </button>
      </div>
      {galleries.length === 0 ? (
        <div className="empty-state">
          <p>You don't have any galleries yet. Create one to get started!</p>
        </div>
      ) : (
        <div className="galleries-grid">
          {galleries.map(gallery => (
            <div key={gallery.id} className="gallery-card" onClick={() => openGallery(gallery)}>
              <h3>{gallery.name}</h3>
              <p>{gallery.description || 'No description'}</p>
              <div className="gallery-meta">
                <span>Created: {new Date(gallery.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const GalleryView = () => (
    <div className="gallery-view">
      <div className="gallery-header">
        <div className="gallery-info">
          <h2>{currentGallery.name}</h2>
          <p>{currentGallery.description || 'No description'}</p>
        </div>
        
        <div className="gallery-actions">
          <div className="view-toggle">
            <button 
              className={`icon-button ${viewMode === 'grid' ? 'active' : ''}`} 
              onClick={() => setViewMode('grid')}
              title="Grid View"
            >
              <span className="material-icons">grid_view</span>
            </button>
            <button 
              className={`icon-button ${viewMode === 'list' ? 'active' : ''}`} 
              onClick={() => setViewMode('list')}
              title="List View"
            >
              <span className="material-icons">view_list</span>
            </button>
          </div>
          
          <button 
            className="button"
            onClick={openEditGalleryModal}
            title="Edit Gallery"
          >
            Edit Gallery
          </button>
          
          {currentGallery.id !== 'default' && (
            <button 
              className="button danger"
              onClick={() => deleteGallery(currentGallery.id)}
              title="Delete Gallery"
            >
              Delete Gallery
            </button>
          )}
          
          <button 
            className="primary-button"
            onClick={() => setIsUploadModalOpen(true)}
            title="Upload Images"
          >
            Upload Images
          </button>
        </div>
      </div>
      
      {galleryImages.length === 0 ? (
        <div className="empty-state">
          <p>This gallery is empty. Upload images to populate it!</p>
          <button 
            className="primary-button"
            onClick={() => setIsUploadModalOpen(true)}
          >
            Upload Images
          </button>
        </div>
      ) : (
        <div className={`images-container ${viewMode}`}>
          {galleryImages.map(image => (
            <div 
              key={image.id} 
              className="image-item" 
              onClick={() => openImageDetails(image)}
            >
              <div className="image-thumbnail">
                <img 
                  src={`http://localhost:5345/uploads/${image.filename}`} 
                  alt={image.title || 'Gallery image'} 
                  loading="lazy" 
                />
              </div>
              <div className="image-info">
                <h3>{image.title || 'Untitled'}</h3>
                {viewMode === 'list' && (
                  <p className="image-description">{image.description || 'No description'}</p>
                )}
                <div className="image-meta">
                  <span>Uploaded: {new Date(image.uploaded_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const ImageDetailsView = () => {
    if (!currentImage) return null;
    
    return (
      <div className="image-details-view">
        <div className="image-display">
          <img 
            src={`http://localhost:5345/uploads/${currentImage.filename}`}
            alt={currentImage.title || 'Gallery image'}
          />
        </div>
        
        <div className="image-details">
          <div className="image-title-section">
            <h2>{currentImage.title || 'Untitled'}</h2>
            <div className="image-actions">
              <button 
                className="button"
                onClick={openEditImageModal}
              >
                Edit Details
              </button>
              <button 
                className="button danger"
                onClick={() => deleteImage(currentImage.id)}
              >
                Delete Image
              </button>
            </div>
          </div>
          
          <p className="image-description">{currentImage.description || 'No description available'}</p>
          
          <div className="image-metadata">
            <div className="metadata-item">
              <strong>Original Filename:</strong> {currentImage.original_filename}
            </div>
            <div className="metadata-item">
              <strong>File Size:</strong> {formatFileSize(currentImage.file_size)}
            </div>
            <div className="metadata-item">
              <strong>Uploaded:</strong> {formatDateTime(currentImage.uploaded_at)}
            </div>
            <div className="metadata-item">
              <strong>Type:</strong> {currentImage.mime_type}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Modals
  const NewGalleryModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Create New Gallery</h2>
        <form onSubmit={(e) => { e.preventDefault(); createGallery(); }}>
          <div className="form-group">
            <label htmlFor="gallery-name">Gallery Name *</label>
            <input 
              id="gallery-name"
              type="text" 
              value={newGalleryName} 
              onChange={(e) => setNewGalleryName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="gallery-desc">Description (optional)</label>
            <textarea 
              id="gallery-desc"
              value={newGalleryDesc}
              onChange={(e) => setNewGalleryDesc(e.target.value)}
            />
          </div>
          
          <div className="modal-actions">
            <button 
              type="button" 
              className="button"
              onClick={() => setIsNewGalleryModalOpen(false)}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="primary-button"
              disabled={!newGalleryName.trim() || isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Gallery'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const EditGalleryModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Edit Gallery</h2>
        <form onSubmit={(e) => { e.preventDefault(); updateGallery(); }}>
          <div className="form-group">
            <label htmlFor="edit-gallery-name">Gallery Name *</label>
            <input 
              id="edit-gallery-name"
              type="text" 
              value={editGalleryName} 
              onChange={(e) => setEditGalleryName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="edit-gallery-desc">Description (optional)</label>
            <textarea 
              id="edit-gallery-desc"
              value={editGalleryDesc}
              onChange={(e) => setEditGalleryDesc(e.target.value)}
            />
          </div>
          
          <div className="modal-actions">
            <button 
              type="button" 
              className="button"
              onClick={() => setIsEditGalleryModalOpen(false)}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="primary-button"
              disabled={!editGalleryName.trim() || isLoading}
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
  const UploadImageModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Upload Image</h2>
        <form onSubmit={uploadImage}>
          <div className="form-group">
            <label htmlFor="image-file">Select Image *</label>
            <input 
              id="image-file"
              type="file" 
              accept=".jpg,.jpeg,.png,.gif,.webp"
              onChange={handleFileChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="image-title">Title (optional)</label>
            <input 
              id="image-title"
              type="text" 
              value={imageTitle}
              onChange={(e) => setImageTitle(e.target.value)}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="image-desc">Description (optional)</label>
            <textarea 
              id="image-desc"
              value={imageDesc}
              onChange={(e) => setImageDesc(e.target.value)}
            />
          </div>
          
          {uploadProgress > 0 && (
            <div className="upload-progress">
              <div 
                className="progress-bar" 
                style={{width: `${uploadProgress}%`}}
              ></div>
              <span>{uploadProgress}%</span>
            </div>
          )}
          
          <div className="modal-actions">
            <button 
              type="button" 
              className="button"
              onClick={() => setIsUploadModalOpen(false)}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="primary-button"
              disabled={!selectedFile || isLoading}
            >
              {isLoading ? 'Uploading...' : 'Upload Image'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const EditImageModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Edit Image Details</h2>
        <form onSubmit={(e) => { e.preventDefault(); updateImage(); }}>
          <div className="form-group">
            <label htmlFor="edit-image-title">Title</label>
            <input 
              id="edit-image-title"
              type="text" 
              value={imageTitle}
              onChange={(e) => setImageTitle(e.target.value)}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="edit-image-desc">Description</label>
            <textarea 
              id="edit-image-desc"
              value={imageDesc}
              onChange={(e) => setImageDesc(e.target.value)}
            />
          </div>
          
          <div className="modal-actions">
            <button 
              type="button" 
              className="button"
              onClick={() => setIsEditImageModalOpen(false)}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="primary-button"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // Helper functions
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
  };

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Main render
  return (
    <div className="app-container">
      <Navigation />
      
      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}
      
      {isLoading && view !== 'gallery' && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <span>Loading...</span>
        </div>
      )}
      
      <main className="app-content">
        {view === 'galleries' && <GalleriesView />}
        {view === 'gallery' && currentGallery && <GalleryView />}
        {view === 'imageDetails' && <ImageDetailsView />}
      </main>
      
      {/* Modals */}
      {isNewGalleryModalOpen && <NewGalleryModal />}
      {isEditGalleryModalOpen && <EditGalleryModal />}
      {isUploadModalOpen && <UploadImageModal />}
      {isEditImageModalOpen && <EditImageModal />}
    </div>
  );
}

// Mount the App to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;

