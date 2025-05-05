import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [posts, setPosts] = useState([]);
    const [newPostContent, setNewPostContent] = useState('');
    const [editingPostId, setEditingPostId] = useState(null);
    const [editedPostContent, setEditedPostContent] = useState('');
    const [userProfile, setUserProfile] = useState({ username: 'default_user', bio: '', profile_picture: '' });
    const [showProfileEdit, setShowProfileEdit] = useState(false);
    const [newBio, setNewBio] = useState('');
    const [newProfilePicture, setNewProfilePicture] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedPost, setSelectedPost] = useState(null); // For viewing a single post with comments
    const [newComment, setNewComment] = useState('');

    useEffect(() => {
        fetchPosts();
        fetchUserProfile();
    }, []);

    const fetchPosts = async () => {
        try {
            const response = await fetch(`/api/posts?q=${searchQuery}`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            setPosts(data);
        } catch (error) {
            console.error('Failed to fetch posts:', error);
            // Handle error appropriately (e.g., display an error message to the user)
        }
    };


    const fetchUserProfile = async () => {
        try {
            const response = await fetch('/api/users/default_user');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            setUserProfile(data);
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
        }
    };


    const createPost = async () => {
        try {
            const response = await fetch('/api/posts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: newPostContent }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const newPost = await response.json();
            setPosts([newPost, ...posts]);
            setNewPostContent(''); // Clear the input field
        } catch (error) {
            console.error('Failed to create post:', error);
            // Handle error appropriately
        }
    };


    const updatePost = async (id) => {
        try {
            const response = await fetch(`/api/posts/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: editedPostContent }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const updatedPost = await response.json();
            setPosts(posts.map(post => (post.id === id ? updatedPost : post)));
            setEditingPostId(null);
            setEditedPostContent('');
            fetchPosts(); // Refresh posts to reflect changes
        } catch (error) {
            console.error('Failed to update post:', error);
            // Handle error appropriately
        }
    };


    const deletePost = async (id) => {
        try {
            const response = await fetch(`/api/posts/${id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            setPosts(posts.filter(post => post.id !== id));
            fetchPosts();  // Refresh posts to reflect changes
        } catch (error) {
            console.error('Failed to delete post:', error);
            // Handle error appropriately
        }
    };


    const likePost = async (id) => {
        try {
            const response = await fetch(`/api/posts/${id}/like`, {
                method: 'POST',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const updatedPost = await response.json();
            setPosts(posts.map(post => (post.id === id ? updatedPost : post)));
            fetchPosts(); // Refresh posts to reflect changes
        } catch (error) {
            console.error('Failed to like post:', error);
        }
    };

    const addComment = async (postId) => {
        try {
            const response = await fetch(`/api/posts/${postId}/comment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ comment: newComment }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const updatedPost = await response.json();
            setPosts(posts.map(post => (post.id === postId ? updatedPost : post)));
            setNewComment('');
            setSelectedPost(updatedPost); // Update the selected post with new comment
            fetchPosts();
        } catch (error) {
            console.error('Failed to add comment:', error);
        }
    };


    const saveProfile = async () => {
        try {
            const response = await fetch('/api/users/default_user', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ bio: newBio, profile_picture: newProfilePicture }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const updatedUser = await response.json();
            setUserProfile(updatedUser);
            setShowProfileEdit(false);
            fetchUserProfile(); // Refresh user profile
        } catch (error) {
            console.error('Failed to update profile:', error);
        }
    };

    const handleSearchChange = (event) => {
        setSearchQuery(event.target.value);
    };

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        fetchPosts();
    };


    const renderPost = (post) => {
        return (
            <div key={post.id} className="post">
                <div className="post-header">
                    <img src={userProfile.profile_picture} alt="Profile" className="profile-picture"/>
                    <span className="post-author">{post.author}</span>
                </div>
                <div className="post-content">
                    {editingPostId === post.id ? (
                        <textarea
                            value={editedPostContent}
                            onChange={(e) => setEditedPostContent(e.target.value)}
                        />
                    ) : (
                        <p>{post.content}</p>
                    )}
                    <p className="post-timestamp">
                        {new Date(post.timestamp).toLocaleString()}
                    </p>

                </div>
                <div className="post-actions">
                    <button onClick={() => likePost(post.id)}>Like ({post.likes})</button>
                    <button onClick={() => setSelectedPost(post)}>View</button>
                    {editingPostId === post.id ? (
                        <>
                            <button onClick={() => updatePost(post.id)}>Save</button>
                            <button onClick={() => setEditingPostId(null)}>Cancel</button>
                        </>
                    ) : (
                        <>
                            <button onClick={() => {
                                setEditingPostId(post.id);
                                setEditedPostContent(post.content);
                            }}>Edit</button>
                            <button onClick={() => deletePost(post.id)}>Delete</button>
                        </>
                    )}
                </div>
            </div>
        );
    };


    return (
        <div className="app-container">
            <header>
                <h1>Microblog</h1>
            </header>

            <nav>
                <button onClick={() => setSelectedPost(null)}>Timeline</button>
                <button onClick={() => setShowProfileEdit(true)}>Edit Profile</button>
            </nav>

            {showProfileEdit ? (
                <div className="profile-edit">
                    <h2>Edit Profile</h2>
                    <input
                        type="text"
                        placeholder="New Bio"
                        value={newBio}
                        onChange={(e) => setNewBio(e.target.value)}
                    />
                    <input
                        type="text"
                        placeholder="New Profile Picture URL"
                        value={newProfilePicture}
                        onChange={(e) => setNewProfilePicture(e.target.value)}
                    />
                    <button onClick={saveProfile}>Save Profile</button>
                    <button onClick={() => setShowProfileEdit(false)}>Cancel</button>
                </div>
            ) : (
                <div className="profile">
                    <img src={userProfile.profile_picture} alt="Profile" className="profile-picture"/>
                    <h2>{userProfile.username}</h2>
                    <p>{userProfile.bio}</p>
                </div>
            )}

            <div className="search-bar">
                <form onSubmit={handleSearchSubmit}>
                    <input
                        type="text"
                        placeholder="Search posts..."
                        value={searchQuery}
                        onChange={handleSearchChange}
                    />
                    <button type="submit">Search</button>
                </form>
            </div>


            {selectedPost ? (
                <div className="single-post-view">
                    <h2>Post Details</h2>
                    {renderPost(selectedPost)}
                    <div className="comments-section">
                        <h3>Comments</h3>
                        {selectedPost.comments.map((comment, index) => (
                            <p key={index}>{comment}</p>
                        ))}
                        <div className="add-comment">
                            <textarea
                                placeholder="Add a comment..."
                                value={newComment}
                                onChange={(e) => setNewComment(e.target.value)}
                            />
                            <button onClick={() => addComment(selectedPost.id)}>Add Comment</button>
                        </div>
                    </div>
                </div>
            ) : (
                <>
                    <div className="post-creation">
                        <textarea
                            placeholder="Write a new post..."
                            value={newPostContent}
                            onChange={(e) => setNewPostContent(e.target.value)}
                        />
                        <button onClick={createPost}>Post</button>
                    </div>

                    <div className="timeline">
                        {posts.map(post => renderPost(post))}
                    </div>
                </>
            )}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
