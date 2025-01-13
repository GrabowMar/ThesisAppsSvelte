
import { serve } from "https://deno.land/std@0.140.0/http/server.ts";

async function handleRequest(req) {
    const url = new URL(req.url);

    if (url.pathname === "/") {
        return new Response(`<!DOCTYPE html><html>  <head>    <title>Deno App</title>  </head>  <body>    <div id="app"></div>    <script type="module">      import App from './src/App.js';      const app = document.getElementById('app');      new App(app);    </script>  </body></html>`, {
            headers: { "content-type": "text/html; charset=utf-8" }
        });
    }

    if (url.pathname.startsWith("/src/")) {
        try {
            const file = await Deno.readFile(`.${url.pathname}`);
            const contentType = url.pathname.endsWith(".js") ? "application/javascript" : "text/plain";
            return new Response(file, { headers: { "content-type": contentType } });
        } catch {
            return new Response("Not found", { status: 404 });
        }
    }

    return new Response("Not found", { status: 404 });
}

console.log("Server running at http://localhost:5181");
await serve(handleRequest, { port: 5181 });
