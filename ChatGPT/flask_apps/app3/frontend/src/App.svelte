<script>
  import { onMount } from "svelte";

  let name = "";
  let email = "";
  let feedback = "";
  let successMessage = "";
  let errorMessage = "";

  const submitFeedback = async () => {
    errorMessage = "";
    successMessage = "";

    if (!name || !email || !feedback) {
      errorMessage = "All fields are required.";
      return;
    }

    try {
      const response = await fetch("http://localhost:5005/submit-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, feedback }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        errorMessage = errorData.error || "An error occurred.";
        return;
      }

      const data = await response.json();
      successMessage = data.message;
      name = email = feedback = ""; // Clear the form
    } catch (err) {
      errorMessage = "Failed to submit feedback. Please try again.";
    }
  };
</script>

<main>
  <h1>Feedback Form</h1>
  {#if successMessage}
    <p style="color: green;">{successMessage}</p>
  {/if}
  {#if errorMessage}
    <p style="color: red;">{errorMessage}</p>
  {/if}

  <form on:submit|preventDefault={submitFeedback}>
    <label>
      Name:
      <input type="text" bind:value={name} required />
    </label>
    <label>
      Email:
      <input type="email" bind:value={email} required />
    </label>
    <label>
      Feedback:
      <textarea bind:value={feedback} required></textarea>
    </label>
    <button type="submit">Submit</button>
  </form>
</main>

<style>
  main {
    font-family: Arial, sans-serif;
    padding: 1rem;
    max-width: 600px;
    margin: auto;
  }
  label {
    display: block;
    margin-bottom: 1rem;
  }
  input, textarea {
    width: 100%;
    padding: 0.5rem;
    margin-top: 0.5rem;
  }
  button {
    padding: 0.5rem 1rem;
  }
</style>
