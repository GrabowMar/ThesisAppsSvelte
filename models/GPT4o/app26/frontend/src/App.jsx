import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

function App() {
  const [carbonFootprint, setCarbonFootprint] = useState(null);
  const [resourceConsumption, setResourceConsumption] = useState({});
  const [challengesCompleted, setChallengesCompleted] = useState(0);
  const [ecoTips, setEcoTips] = useState([]);
  const [communityRank, setCommunityRank] = useState(null);

  // Fetch carbon footprint
  useEffect(() => {
    fetch("/api/carbon-footprint?username=sample_user")
      .then((response) => response.json())
      .then((data) => setCarbonFootprint(data.carbon_footprint))
      .catch((error) => console.error("Error fetching carbon footprint:", error));
  }, []);

  // Fetch resource consumption
  useEffect(() => {
    fetch("/api/resource-consumption?username=sample_user")
      .then((response) => response.json())
      .then((data) => setResourceConsumption(data))
      .catch((error) =>
        console.error("Error fetching resource consumption:", error)
      );
  }, []);

  // Fetch eco tips
  useEffect(() => {
    fetch("/api/eco-tips?username=sample_user")
      .then((response) => response.json())
      .then((data) => setEcoTips(data.eco_tips))
      .catch((error) => console.error("Error fetching eco-tips:", error));
  }, []);

  // Fetch community rank
  useEffect(() => {
    fetch("/api/community-rank?username=sample_user")
      .then((response) => response.json())
      .then((data) => setCommunityRank(data.community_rank))
      .catch((error) => console.error("Error fetching community rank:", error));
  }, []);

  const handleChallengeCreate = () => {
    fetch("/api/challenges", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "sample_user" }),
    })
      .then((response) => response.json())
      .then((data) => {
        alert(data.message);
        setChallengesCompleted(data.challenges_completed);
      })
      .catch((error) => console.error("Error creating challenge:", error));
  };

  return (
    <div className="App">
      <header>
        <h1>Environmental Sustainability Tracker</h1>
      </header>
      <main>
        <section>
          <h2>Carbon Footprint</h2>
          <p>
            Current Carbon Footprint: {carbonFootprint || "Loading..."} kg CO2
          </p>
        </section>

        <section>
          <h2>Resource Consumption</h2>
          <p>Water: {resourceConsumption.water || "Loading..."} L/day</p>
          <p>Electricity: {resourceConsumption.electricity || "Loading..."} kWh/month</p>
        </section>

        <section>
          <h2>Sustainability Challenges</h2>
          <button onClick={handleChallengeCreate}>Complete a Challenge</button>
          <p>Challenges Completed: {challengesCompleted || "0"}</p>
        </section>

        <section>
          <h2>Eco-Friendly Tips</h2>
          <ul>
            {ecoTips.length > 0
              ? ecoTips.map((tip, index) => <li key={index}>{tip}</li>)
              : "Loading tips..."}
          </ul>
        </section>

        <section>
          <h2>Community Rank</h2>
          <p>
            Your rank in the community:{" "}
            {communityRank !== null ? communityRank : "Loading..."}
          </p>
        </section>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
