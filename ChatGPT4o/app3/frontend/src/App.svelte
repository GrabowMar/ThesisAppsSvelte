<script>
  import { onMount } from 'svelte';
  let name = '';
  let email = '';
  let message = '';
  let feedbacks = [];
  let successMessage = '';
  let errorMessage = '';

  const submitFeedback = async () => {
    successMessage = '';
    errorMessage = '';
    
    if (!name || !email || !message) {
      errorMessage = 'All fields are required!';
      return;
    }

    try {
      const res = await fetch('http://localhost:5005/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, message })
      });
      
      const data = await res.json();
      if (res.ok) {
        successMessage = data.message;
        name = '';
        email = '';
        message = '';
        fetchFeedbacks();
      } else {
        errorMessage = data.error || 'An error occurred';
      }
    } catch (error) {
      errorMessage = 'Failed to submit feedback';
    }
  };

  const fetchFeedbacks = async () => {
    try {
      const res = await fetch('http://localhost:5005/feedbacks');
      feedbacks = await res.json();
    } catch (error) {
      console.error('Error fetching feedbacks:', error);
    }
  };

  onMount(fetchFeedbacks);
</script>

<main>
  <h1>Feedback Form</h1>
  {#if successMessage}<p class="success">{successMessage}</p>{/if}
  {#if errorMessage}<p class="error">{errorMessage}</p>{/if}
  <form on:submit|preventDefault={submitFeedback}>
    <input type="text" bind:value={name} placeholder="Your Name" required />
    <input type="email" bind:value={email} placeholder="Your Email" required />
    <textarea bind:value={message} placeholder="Your Feedback" required></textarea>
    <button type="submit">Submit</button>
  </form>

  <h2>Previous Feedback</h2>
  <ul>
    {#each feedbacks as fb}
      <li><strong>{fb.name}</strong>: {fb.message}</li>
    {/each}
  </ul>
</main>

<style>
  main { max-width: 500px; margin: auto; padding: 20px; }
  form { display: flex; flex-direction: column; gap: 10px; }
  input, textarea { padding: 8px; font-size: 1rem; }
  button { background: blue; color: white; padding: 10px; }
  .success { color: green; }
  .error { color: red; }
</style>