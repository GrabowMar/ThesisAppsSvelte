import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'

function App() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        rating: '',
        comments: ''
    })
    const [errors, setErrors] = useState({})
    const [isSubmitted, setIsSubmitted] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        
        // Client-side validation
        const newErrors = {}
        if (!formData.name) newErrors.name = 'Name is required'
        if (!formData.email) {
            newErrors.email = 'Email is required'
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'Invalid email format'
        }
        if (!formData.rating) newErrors.rating = 'Rating is required'
        if (!formData.comments) newErrors.comments = 'Comments are required'
        
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors)
            return
        }

        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })

            if (!response.ok) {
                const errorData = await response.json()
                setErrors(errorData.errors || {})
                return
            }

            setIsSubmitted(true)
            setErrors({})
        } catch (error) {
            console.error('Submission error:', error)
            setErrors({ general: 'Failed to submit feedback. Please try again.' })
        }
    }

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
        setErrors({
            ...errors,
            [e.target.name]: null
        })
    }

    return (
        <div className="app-container">
            {!isSubmitted ? (
                <form onSubmit={handleSubmit} className="feedback-form">
                    <h1>Share Your Feedback</h1>
                    
                    {errors.general && <div className="error-message">{errors.general}</div>}

                    <div className="form-group">
                        <label htmlFor="name">Name:</label>
                        <input
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            className={errors.name ? 'error' : ''}
                        />
                        {errors.name && <span className="error-message">{errors.name}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="email">Email:</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleChange}
                            className={errors.email ? 'error' : ''}
                        />
                        {errors.email && <span className="error-message">{errors.email}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="rating">Rating (1-5):</label>
                        <select
                            id="rating"
                            name="rating"
                            value={formData.rating}
                            onChange={handleChange}
                            className={errors.rating ? 'error' : ''}
                        >
                            <option value="">Select rating</option>
                            {[1, 2, 3, 4, 5].map(num => (
                                <option key={num} value={num}>{num}</option>
                            ))}
                        </select>
                        {errors.rating && <span className="error-message">{errors.rating}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="comments">Comments:</label>
                        <textarea
                            id="comments"
                            name="comments"
                            value={formData.comments}
                            onChange={handleChange}
                            className={errors.comments ? 'error' : ''}
                            rows="4"
                        />
                        {errors.comments && <span className="error-message">{errors.comments}</span>}
                    </div>

                    <button type="submit" className="submit-btn">Submit Feedback</button>
                </form>
            ) : (
                <div className="success-message">
                    <h2>Thank you for your feedback! ✅</h2>
                    <button onClick={() => setIsSubmitted(false)}>Submit another feedback</button>
                </div>
            )}
        </div>
    )
}

// Mounting logic
const root = createRoot(document.getElementById('root'))
root.render(<App />)
