```markdown
# Forum Application Template - Flask + Svelte

## Important Implementation Notes

1. Generate web app with properly implemented key features mentioned below.
2. Try to keep all changes within **app.py** and **App.svelte** files.
3. Try to write feature complete production ready app, with comments, fails states, etc.
4. **Note:** Multipage routing is possible within these files. On the backend, you can define multiple routes (e.g., `/login`, `/register`, `/dashboard`, etc.) in **app.py**. On the frontend, client-side routing can be managed within **App.svelte** using conditional rendering or a routing library, all within the single-file constraint.
## Project Description

**Forum System**  
A discussion platform built with Flask and Svelte, featuring thread and comment management.

**Required Features:**
- **Multipage Routing:** Extendable routing on both backend and frontend for additional pages/views
- SImple and modern UI

**Template Specific:**

- Thread creation/viewing
- Comment system
- Categories
- Sorting
- Thread search

## Implementation Structure

### Project Layout

```plaintext
app/
├── backend/
│   ├── app.py              # ALL backend logic
│   ├── Dockerfile          # (optional)
│   └── requirements.txt    # (generated if needed)
│
├── frontend/
│   ├── src/
│   │   ├── App.svelte      # ALL frontend logic (multipage routing supported)
│   │   └── main.js         # (optional)
│   ├── Dockerfile          # (optional)
│   ├── package.json        # (generated if needed)
│   └── vite.config.js      # (required for port config)
│
└── docker-compose.yml      # (optional)
```

### Core Files Structure

#### Backend (app.py)

```python
# In app.py, you can define multiple routes to support different pages and API endpoints.

if __name__ == '__main__':
    # Replace 'XXXX' with the desired backend port.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)

```svelte
<script>
  // Implement client-side routing here using conditional logic
  // or by integrating a routing library, all within this single file.
</script>

<main>
  <!-- Render different views based on routing logic -->
</main>

<style>
  /* Styles */
</style>
```

## Response Protocol

### Protocol Steps

1. **Port Configuration Prompt**
   - Request port numbers for backend and frontend.
   - Replace `XXXX` (backend) and `YYYY` (frontend) placeholders.
   - **Example format:** "Please provide two port numbers for backend and frontend."

2. **Backend Generation Prompt**
   - Request complete **app.py** code generation.
   - Must include all specified backend features.
   - Must list required pip dependencies.
   - Wait for user confirmation before proceeding.
   - Aim for best practices and professionalism.
   - **Example format:** "Generate the Flask backend code with the specified features:"

3. **Frontend Generation Prompt**
   - Request complete **App.svelte** code generation.
   - Must include all specified frontend features.
   - Must list required npm dependencies.
   - Aim for best practices and professionalism.
   - **Example format:** "Generate the Svelte frontend code with the specified features:"

**Very important:** Your app should be feature rich and production ready.
```