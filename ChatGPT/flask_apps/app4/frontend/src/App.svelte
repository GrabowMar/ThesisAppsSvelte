<script>
  import { onMount } from 'svelte';

  let name = "";
  let email = "";
  let message = "";
  let rating = 5;
  let feedbackMessage = "";
  let isSubmitting = false;

  async function submitFeedback() {
    if (!name || !email || !message || !rating) {
      feedbackMessage = "All fields are required.";
      return;
    }

    isSubmitting = true;
    feedbackMessage = "";

    try {
      const response = await fetch("http://localhost:5005/submit_feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message, rating }),
      });

      const result = await response.json();
      feedbackMessage = result.message || result.error;

      if (response.ok) {
        name = "";
        email = "";
        message = "";
        rating = 5;
      }
    } catch (error) {
      feedbackMessage = "Error submitting feedback.";
    } finally {
      isSubmitting = false;
    }
  }
</script>

<main class="container">
  <h1>Feedback Form</h1>
  
  <label>Name</label>
  <input type="text" bind:value={name} placeholder="Your Name" required />

  <label>Email</label>
  <input type="email" bind:value={email} placeholder="Your Email" required />

  <label>Message</label>
  <textarea bind:value={message} placeholder="Your Feedback" required></textarea>

  <label>Rating</label>
  <input type="number" bind:value={rating} min="1" max="5" />

  <button on:click={submitFeedback} disabled={isSubmitting}>
    {isSubmitting ? "Submitting..." : "Submit Feedback"}
  </button>

  {#if feedbackMessage}
    <p class={feedbackMessage.includes("successfully") ? "success" : "error"}>
      {feedbackMessage}
    </p>
  {/if}
</main>

<style>
  .container {
    max-width: 400px;
    margin: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }
  input, textarea, button {
    margin: 5px 0;
    padding: 10px;
    width: 100%;
  }
  .success { color: green; }
  .error { color: red; }
</style>
