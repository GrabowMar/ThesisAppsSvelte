<script>
  import { onMount } from "svelte";
  import { io } from "socket.io-client";
  import { writable } from "svelte/store";

  let username = "";
  let room = "";
  let message = "";
  let messages = writable([]);
  let socket;
  let page = "login";

  function connectSocket() {
    socket = io("http://localhost:5003");

    socket.on("message", (data) => {
      messages.update((msgs) => [...msgs, data]);
    });
  }

  async function loginUser(user, pass) {
    const res = await fetch("http://localhost:5003/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, password: pass })
    });
    const data = await res.json();
    if (res.ok) {
      username = user;
      page = "chat";
      connectSocket();
    } else {
      alert(data.error);
    }
  }

  function joinChatRoom() {
    if (room) {
      socket.emit("join", { username, room });
    }
  }

  function sendMessage() {
    if (message.trim() !== "") {
      socket.emit("message", { username, room, message });
      message = "";
    }
  }
</script>

<main>
  {#if page === "login"}
    <div>
      <h2>Login</h2>
      <input type="text" placeholder="Username" bind:value={username} />
      <input type="password" placeholder="Password" bind:value={password} />
      <button on:click={() => loginUser(username, password)}>Login</button>
    </div>
  {:else}
    <div>
      <h2>Chat Room</h2>
      <input type="text" placeholder="Room" bind:value={room} />
      <button on:click={joinChatRoom}>Join</button>

      <div>
        {#each $messages as msg}
          <p><strong>{msg.user}:</strong> {msg.message}</p>
        {/each}
      </div>

      <input type="text" placeholder="Message" bind:value={message} on:keypress={(e) => e.key === 'Enter' && sendMessage()} />
      <button on:click={sendMessage}>Send</button>
    </div>
  {/if}
</main>

<style>
  main {
    padding: 20px;
  }
  input, button {
    display: block;
    margin: 10px 0;
  }
</style>