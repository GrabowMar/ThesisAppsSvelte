<script>
  let message = 'Loading...';

  async function fetchMessage() {
    try {
      const response = await fetch('http://localhost:5068/');
      const data = await response.json();
      message = data.message;
    } catch (error) {
      message = 'Error connecting to ChatGPTo1 backend';
    }
  }

  fetchMessage();
</script>

<main>
  <h1>ChatGPTo1 App</h1>
  <p class="message">{message}</p>
</main>

<style>
  main {
    text-align: center;
    padding: 2em;
  }
  h1 {
    color: #333;
    font-size: 2em;
    margin-bottom: 0.5em;
  }
  .message {
    color: #444;
    font-size: 1.2em;
    margin: 1em;
  }
</style>
