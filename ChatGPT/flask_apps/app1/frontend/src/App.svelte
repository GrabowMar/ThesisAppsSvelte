
<script>
  let email = '';
  let password = '';
  let message = '';

  async function register() {
    const response = await fetch('http://localhost:5001/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();
    message = data.message;
  }

  async function login() {
    const response = await fetch('http://localhost:5001/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();
    message = data.token ? 'Login successful' : data.message;
  }
</script>

<main>
  <h1>Login App</h1>
  <input type="email" bind:value={email} placeholder="Email" />
  <input type="password" bind:value={password} placeholder="Password" />
  <button on:click={register}>Register</button>
  <button on:click={login}>Login</button>
  <p>{message}</p>
</main>

<style>
  main {
    text-align: center;
    max-width: 400px;
    margin: auto;
  }
  input, button {
    display: block;
    margin: 10px auto;
    padding: 10px;
  }
</style>
