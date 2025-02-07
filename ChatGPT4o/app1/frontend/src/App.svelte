<script>
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';

  const username = writable('');
  const password = writable('');
  const message = writable('');
  const loggedIn = writable(false);
  const currentUser = writable('');
  const backendUrl = 'http://localhost:5001';

  async function register() {
    const response = await fetch(`${backendUrl}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: $username, password: $password })
    });
    const data = await response.json();
    message.set(data.message || data.error);
  }

  async function login() {
    const response = await fetch(`${backendUrl}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: $username, password: $password })
    });
    const data = await response.json();
    if (response.ok) {
      loggedIn.set(true);
      currentUser.set($username);
      message.set('Login successful');
    } else {
      message.set(data.error);
    }
  }

  async function logout() {
    await fetch(`${backendUrl}/logout`, { method: 'POST', credentials: 'include' });
    loggedIn.set(false);
    currentUser.set('');
    message.set('Logged out successfully');
  }

  async function checkStatus() {
    const response = await fetch(`${backendUrl}/status`, { credentials: 'include' });
    const data = await response.json();
    loggedIn.set(data.loggedIn);
    currentUser.set(data.username || '');
  }

  onMount(checkStatus);
</script>

<main>
  {#if $loggedIn}
    <h2>Welcome, {$currentUser}!</h2>
    <button on:click={logout}>Logout</button>
  {:else}
    <h2>Login / Register</h2>
    <input type="text" placeholder="Username" bind:value={$username}>
    <input type="password" placeholder="Password" bind:value={$password}>
    <button on:click={login}>Login</button>
    <button on:click={register}>Register</button>
    <p>{$message}</p>
  {/if}
</main>

<style>
  main {
    max-width: 300px;
    margin: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  input, button {
    padding: 10px;
    font-size: 1rem;
  }
</style>
