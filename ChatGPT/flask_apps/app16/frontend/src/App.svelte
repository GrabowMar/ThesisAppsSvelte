
<script>
  let message = 'Loading...';

  async function fetchMessage() {
    try {
      const response = await fetch('http://localhost:5032/');
      const data = await response.json();
      message = data.message;
    } catch (error) {
      message = 'Error connecting to backend';
    }
  }

  fetchMessage();
</script>

<main>
  <p class="message">{message}</p>
</main>

<style>
  main {
    text-align: center;
    padding: 2em;
  }
  .message {
    color: #444;
    font-size: 1.2em;
    margin: 1em;
  }
</style>
