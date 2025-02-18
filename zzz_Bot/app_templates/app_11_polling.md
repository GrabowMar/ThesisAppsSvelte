```markdown
# Polling Application Template - Flask + react

## Important Implementation Notes

1. Generate web app with properly implemented key features mentioned below.
2. Try to keep all changes within **app.py** , **App.jsx** and **App.css** files.
3. Try to write feature complete production ready app, with comments, fails states, etc.
4. **Note:** Multipage routing is possible within these files. On the backend, you can define multiple routes (e.g., `/login`, `/register`, `/dashboard`, etc.) in **app.py**. On the frontend, client-side routing can be managed within **App.jsx** using conditional rendering or a routing library, all within the single-file constraint.
## Project Description

**Polling System**  
A voting application built with Flask and react, featuring poll creation and voting functionality.

**Required Features:**
- **Multipage Routing:** Extendable routing on both backend and frontend for additional pages/views
- SImple and modern UI

**Template Specific:**

- Poll creation
- Vote casting
- Results display
- Analytics
- Time-limited polls

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
│   │   ├── App.jsx      # ALL frontend logic (with potential multipage routing)
│   │   ├── main.jsx         # (optional)
│   │   └── App.css         # (optional)
│   ├── Dockerfile          # (optional)
│   ├── package.json        # (generated if needed)
│   └── vite.config.js      # (required for port config)
│
└── docker-compose.yml      # (optional)
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
   - Must list required pip dependencies in form of requirements.txt.
   - Wait for user confirmation before proceeding.
   - Aim for best practices and professionalism.


3. **Frontend Generation Prompt**
   - Request complete **App.jsx** code generation.
   - Must include all specified frontend features.
   - Must list required npm dependencies in form of package.json (and vite.config.js if necessary)
   - Aim for best practices and professionalism.
   - Request complete **App.css** code generation.


**Very important:** Your app should be feature rich and production ready.
```