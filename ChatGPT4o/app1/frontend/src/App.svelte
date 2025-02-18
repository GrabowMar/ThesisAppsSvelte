<script>
    import { onMount } from "svelte";
    import { writable } from "svelte/store";
    
    let route = "login"; // Controls page navigation
    let username = "";
    let password = "";
    let errorMessage = "";
    let successMessage = "";
    let user = writable(null); // Stores logged-in user session

    async function register() {
        errorMessage = "";
        successMessage = "";
        if (!username || !password) {
            errorMessage = "Username and password are required.";
            return;
        }
        
        let response = await fetch("http://localhost:5001/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        let data = await response.json();
        if (response.ok) {
            successMessage = "Registration successful! You can now log in.";
            username = "";
            password = "";
            route = "login";
        } else {
            errorMessage = data.error || "Registration failed.";
        }
    }

    async function login() {
        errorMessage = "";
        if (!username || !password) {
            errorMessage = "Username and password are required.";
            return;
        }

        let response = await fetch("http://localhost:5001/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        let data = await response.json();
        if (response.ok) {
            user.set(data.username);
            route = "dashboard";
        } else {
            errorMessage = data.error || "Login failed.";
        }
    }

    async function logout() {
        await fetch("http://localhost:5001/logout", { method: "POST" });
        user.set(null);
        route = "login";
    }

    async function fetchDashboard() {
        let response = await fetch("http://localhost:5001/dashboard", { method: "GET" });
        let data = await response.json();
        if (!response.ok) {
            logout();
        } else {
            user.set(data.message);
        }
    }

    onMount(() => {
        fetchDashboard();
    });
</script>

<main>
    {#if route === "login"}
        <h2>Login</h2>
        <input type="text" placeholder="Username" bind:value={username} />
        <input type="password" placeholder="Password" bind:value={password} />
        <button on:click={login}>Login</button>
        <p>Don't have an account? <a href="#" on:click={() => route = "register"}>Register</a></p>
        {#if errorMessage}<p class="error">{errorMessage}</p>{/if}
    {/if}

    {#if route === "register"}
        <h2>Register</h2>
        <input type="text" placeholder="Username" bind:value={username} />
        <input type="password" placeholder="Password" bind:value={password} />
        <button on:click={register}>Register</button>
        <p>Already have an account? <a href="#" on:click={() => route = "login"}>Login</a></p>
        {#if errorMessage}<p class="error">{errorMessage}</p>{/if}
        {#if successMessage}<p class="success">{successMessage}</p>{/if}
    {/if}

    {#if route === "dashboard"}
        <h2>Dashboard</h2>
        <p>Welcome, {$user}!</p>
        <button on:click={logout}>Logout</button>
    {/if}
</main>

<style>
    body {
        font-family: Arial, sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
    }
    input, button {
        display: block;
        margin: 5px;
        padding: 10px;
        width: 200px;
    }
    .error {
        color: red;
    }
    .success {
        color: green;
    }
</style>