
class App {
    constructor(target) {
        this.message = 'Loading...';
        this.target = target;
        this.render();
        this.fetchMessage();
    }

    async fetchMessage() {
        try {
            const response = await fetch('http://localhost:5002/');
            const data = await response.json();
            this.message = data.message;
            this.render();
        } catch (error) {
            this.message = 'Error connecting to backend';
            this.render();
        }
    }

    render() {
        this.target.innerHTML = `
            <div class="app">
                <p class="message">${this.message}</p>
            </div>
            <style>
                .app {{
                    text-align: center;
                    padding: 2em;
                }}
                .message {{
                    color: #444;
                    font-size: 1.2em;
                    margin: 1em;
                }}
            </style>
        `;
    }
}

export default App;
