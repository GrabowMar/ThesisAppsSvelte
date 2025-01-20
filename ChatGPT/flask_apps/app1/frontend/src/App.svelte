<script>
  import { onMount } from 'svelte';
  let username = '';
  let password = '';
  let message = '';
  let isRegister = false;

  const apiBase = 'http://localhost:5001';

  async function handleSubmit() {
    const endpoint = isRegister ? '/register' : '/login';
    const response = await fetch(`${apiBase}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    message = result.message;
    if (response.ok) {
      if (!isRegister) {
        alert('Logged in successfully!');
      } else {
        username = '';
        password = '';
      }
    }
  }

  async function logout() {
    const response = await fetch(`${apiBase}/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    const result = await response.json();
    message = result.message;
  }
</script>

<main>
  <h1>{isRegister ? 'Register' : 'Login'}</h1>
  <form on:submit|preventDefault={handleSubmit}>
    <input
      type="text"
      placeholder="Username"
      bind:value={username}
      required
    />
    <input
      type="password"
      placeholder="Password"
      bind:value={password}
      required
    />
    <button type="submit">{isRegister ? 'Register' : 'Login'}</button>
  </form>
  <button on:click={() => (isRegister = !isRegister)}>
    Switch to {isRegister ? 'Login' : 'Register'}
  </button>
  <button on:click={logout}>Logout</button>
  <p>{message}</p>
</main>

<style>
  main {
    max-width: 400px;
    margin: 50px auto;
    font-family: Arial, sans-serif;
    text-align: center;
  }
  input {
    display: block;
    margin: 10px auto;
    padding: 10px;
    width: 80%;
  }
  button {
    margin: 10px;
    padding: 10px 20px;
  }
  p {
    color: red;
  }
</style>
