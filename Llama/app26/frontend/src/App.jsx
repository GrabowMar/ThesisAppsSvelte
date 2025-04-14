// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [carbonFootprint, setCarbonFootprint] = useState([]);
    const [sustainabilityChallenges, setSustainabilityChallenges] = useState([]);
    const [resourceConsumption, setResourceConsumption] = useState([]);
    const [ecoFriendlyTips, setEcoFriendlyTips] = useState([]);
    const [progress, setProgress] = useState([]);
    const [communityImpact, setCommunityImpact] = useState([]);
    const [recyclingAndWasteReduction, setRecyclingAndWasteReduction] = useState([]);

    useEffect(() => {
        fetch('/api/carbon-footprint')
            .then(response => response.json())
            .then(data => setCarbonFootprint(data));

        fetch('/api/sustainability-challenges')
            .then(response => response.json())
            .then(data => setSustainabilityChallenges(data));

        fetch('/api/resource-consumption')
            .then(response => response.json())
            .then(data => setResourceConsumption(data));

        fetch('/api/eco-friendly-tips')
            .then(response => response.json())
            .then(data => setEcoFriendlyTips(data));

        fetch('/api/progress')
            .then(response => response.json())
            .then(data => setProgress(data));

        fetch('/api/community-impact')
            .then(response => response.json())
            .then(data => setCommunityImpact(data));

        fetch('/api/recycling-and-waste-reduction')
            .then(response => response.json())
            .then(data => setRecyclingAndWasteReduction(data));
    }, []);

    const handleCarbonFootprintSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.target);
        fetch('/api/carbon-footprint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                value: data.get('carbonFootprintValue')
            })
        })
            .then(response => response.json())
            .then(data => setCarbonFootprint([...carbonFootprint, data]));
    };

    const handleSustainabilityChallengeSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.target);
        fetch('/api/sustainability-challenges', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                challenge: data.get('sustainabilityChallenge')
            })
        })
            .then(response => response.json())
            .then(data => setSustainabilityChallenges([...sustainabilityChallenges, data]));
    };

    const handleResourceConsumptionSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.target);
        fetch('/api/resource-consumption', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                value: data.get('resourceConsumptionValue')
            })
        })
            .then(response => response.json())
            .then(data => setResourceConsumption([...resourceConsumption, data]));
    };

    const handleProgressSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.target);
        fetch('/api/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                value: data.get('progressValue')
            })
        })
            .then(response => response.json())
            .then(data => setProgress([...progress, data]));
    };

    const handleRecyclingAndWasteReductionSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.target);
        fetch('/api/recycling-and-waste-reduction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                value: data.get('recyclingAndWasteReductionValue')
            })
        })
            .then(response => response.json())
            .then(data => setRecyclingAndWasteReduction([...recyclingAndWasteReduction, data]));
    };

    return (
        <div className="App">
            <h1>Environmental Impact Tracking Application</h1>
            <section>
                <h2>Carbon Footprint</h2>
                <ul>
                    {carbonFootprint.map((item, index) => (
                        <li key={index}>{item.value}</li>
                    ))}
                </ul>
                <form onSubmit={handleCarbonFootprintSubmit}>
                    <input type="number" name="carbonFootprintValue" placeholder="Enter carbon footprint value" />
                    <button type="submit">Submit</button>
                </form>
            </section>
            <section>
                <h2>Sustainability Challenges</h2>
                <ul>
                    {sustainabilityChallenges.map((item, index) => (
                        <li key={index}>{item.challenge}</li>
                    ))}
                </ul>
                <form onSubmit={handleSustainabilityChallengeSubmit}>
                    <input type="text" name="sustainabilityChallenge" placeholder="Enter sustainability challenge" />
                    <button type="submit">Submit</button>
                </form>
            </section>
            <section>
                <h2>Resource Consumption</h2>
                <ul>
                    {resourceConsumption.map((item, index) => (
                        <li key={index}>{item.value}</li>
                    ))}
                </ul>
                <form onSubmit={handleResourceConsumptionSubmit}>
                    <input type="number" name="resourceConsumptionValue" placeholder="Enter resource consumption value" />
                    <button type="submit">Submit</button>
                </form>
            </section>
            <section>
                <h2>Eco-Friendly Tips</h2>
                <ul>
                    {ecoFriendlyTips.map((item, index) => (
                        <li key={index}>{item}</li>
                    ))}
                </ul>
            </section>
            <section>
                <h2>Progress</h2>
                <ul>
                    {progress.map((item, index) => (
                        <li key={index}>{item.value}</li>
                    ))}
                </ul>
                <form onSubmit={handleProgressSubmit}>
                    <input type="number" name="progressValue" placeholder="Enter progress value" />
                    <button type="submit">Submit</button>
                </form>
            </section>
            <section>
                <h2>Community Impact</h2>
                <ul>
                    {communityImpact.map((item, index) => (
                        <li key={index}>{item}</li>
                    ))}
                </ul>
            </section>
            <section>
                <h2>Recycling and Waste Reduction</h2>
                <ul>
                    {recyclingAndWasteReduction.map((item, index) => (
                        <li key={index}>{item.value}</li>
                    ))}
                </ul>
                <form onSubmit={handleRecyclingAndWasteReductionSubmit}>
                    <input type="number" name="recyclingAndWasteReductionValue" placeholder="Enter recycling and waste reduction value" />
                    <button type="submit">Submit</button>
                </form>
            </section>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
