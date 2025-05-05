import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
    const [question, setQuestion] = useState('');
    const [option1, setOption1] = useState('');
    const [option2, setOption2] = useState('');
    const [expiresIn, setExpiresIn] = useState('');
    const [pollId, setPollId] = useState('');
    const [pollResults, setPollResults] = useState({});

    const createPoll = async () => {
        try {
            const response = await axios.post('/api/polls', {
                question,
                option1,
                option2,
                expires_in: expiresIn
            });
            setPollId(response.data.id);
        } catch (error) {
            console.error(error);
        }
    };

    const castVote = async (option) => {
        try {
            await axios.post(`/api/polls/${pollId}/votes`, { option });
        } catch (error) {
            console.error(error);
        }
    };

    const getPollResults = async () => {
        try {
            const response = await axios.get(`/api/polls/${pollId}/results`);
            setPollResults(response.data);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div>
            <h1>Create Poll</h1>
            <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Question" />
            <input type="text" value={option1} onChange={(e) => setOption1(e.target.value)} placeholder="Option 1" />
            <input type="text" value={option2} onChange={(e) => setOption2(e.target.value)} placeholder="Option 2" />
            <input type="number" value={expiresIn} onChange={(e) => setExpiresIn(e.target.value)} placeholder="Expires in (minutes)" />
            <button onClick={createPoll}>Create Poll</button>
            {pollId && (
                <div>
                    <h2>Poll Results</h2>
                    <p>Option 1: {pollResults.option1} ({pollResults.option1_votes} votes)</p>
                    <p>Option 2: {pollResults.option2} ({pollResults.option2_votes} votes)</p>
                    <button onClick={() => castVote(pollResults.option1)}>Vote for Option 1</button>
                    <button onClick={() => castVote(pollResults.option2)}>Vote for Option 2</button>
                    <button onClick={getPollResults}>Get Poll Results</button>
                </div>
            )}
        </div>
    );
}

export default App;
