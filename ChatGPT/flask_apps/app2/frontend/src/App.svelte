<script>
  import { onMount } from "svelte";

  let socket;
  let username = "";
  let room = "";
  let message = "";
  let messages = [];
  let isConnected = false;

  const connect = () => {
      socket = io("http://localhost:5003");

      socket.on("message", (data) => {
          if (typeof data === "string") {
              messages = [...messages, { system: true, text: data }];
          } else {
              messages = [...messages, { username: data.username, text: data.message }];
          }
      });
  };

  const joinRoom = () => {
      if (username && room) {
          connect();
          socket.emit("join", { username, room });
          isConnected = true;
      }
  };

  const sendMessage = () => {
      if (message) {
          socket.emit("message", { message });
          message = "";
      }
  };

  const leaveRoom = () => {
      socket.emit("leave", {});
      socket.disconnect();
      isConnected = false;
      messages = [];
  };
</script>

<main>
  {#if !isConnected}
  <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

      <div>
          <input type="text" bind:value={username} placeholder="Enter your username" />
          <input type="text" bind:value={room} placeholder="Enter room name" />
          <button on:click={joinRoom}>Join Room</button>
      </div>
  {:else}
      <div>
          <div>
              <h2>Room: {room}</h2>
              <button on:click={leaveRoom}>Leave Room</button>
          </div>
          <div>
              <ul>
                  {#each messages as msg}
                      <li>{msg.system ? msg.text : `${msg.username}: ${msg.text}`}</li>
                  {/each}
              </ul>
          </div>
          <div>
              <input type="text" bind:value={message} placeholder="Type a message" />
              <button on:click={sendMessage}>Send</button>
          </div>
      </div>
  {/if}
</main>

<style>
  main {
      font-family: Arial, sans-serif;
      margin: 20px;
  }

  input {
      margin: 5px;
      padding: 5px;
  }

  button {
      margin: 5px;
      padding: 5px;
  }

  ul {
      list-style: none;
      padding: 0;
  }

  li {
      margin: 5px 0;
  }
</style>
