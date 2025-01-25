const express = require("express");
const app = express();
const port = process.env.PORT || 5507;

app.get("/", (req, res) => {
    res.send(`Frontend running on port ${port}`);
});

app.get("/health", (req, res) => {
    res.send("healthy");
});

app.listen(port, () => {
    console.log(`Frontend listening on port ${port}`);
});