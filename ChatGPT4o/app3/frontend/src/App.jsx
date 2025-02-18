import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [formData, setFormData] = useState({ name: "", email: "", feedback: "" });
  const [feedbackList, setFeedbackList] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("http://localhost:5005/feedback")
      .then((res) => res.json())
      .then((data) => setFeedbackList(data))
      .catch((err) => console.error("Error fetching feedback:", err));
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:5005/submit-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage("Feedback submitted successfully!");
        setFeedbackList([...feedbackList, formData]);
        setFormData({ name: "", email: "", feedback: "" });
      } else {
        setMessage(data.error);
      }
    } catch (error) {
      setMessage("Error submitting feedback.");
    }
  };

  return (
    <div className="container">
      <h1>Feedback Form</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="name" placeholder="Name" value={formData.name} onChange={handleChange} required />
        <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} required />
        <textarea name="feedback" placeholder="Your Feedback" value={formData.feedback} onChange={handleChange} required></textarea>
        <button type="submit">Submit</button>
      </form>
      {message && <p className="message">{message}</p>}
      <h2>Feedback Received</h2>
      <ul>
        {feedbackList.map((item, index) => (
          <li key={index}><strong>{item.name}</strong>: {item.feedback}</li>
        ))}
      </ul>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

export default App;