```markdown
# CRUD Microblog Application Template - Flask + react

## Important Implementation Notes

1. Generate web app with properly implemented key features mentioned below.
2. Try to keep all changes within **app.py** , **App.jsx** and **App.css** files.
3. Try to write feature complete production ready app, with comments, fails states, etc.
4. **Note:** Multipage routing is possible within these files. On the backend, you can define multiple routes (e.g., `/login`, `/register`, `/dashboard`, etc.) in **app.py**. On the frontend, client-side routing can be managed within **App.jsx** using conditional rendering or a routing library, all within the single-file constraint.
5. Mounting Logic: The App.jsx file must include mounting logic. This means it should import ReactDOM from react-dom/client and use it to attach the main App component to the DOM element with the id "root".
## Project Description

**CRUD Microblog System**  
A microblog system built with Flask and react.

**Required Features:**
- **Multipage Routing:** Extendable routing on both backend and frontend for additional pages/views
- SImple and modern UI

**Template Specific:**

- Post creation and management (CRUD)
- User profile management
- Post timeline/feed
- Post interactions (likes/comments)
- Post search

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
   - Use `XXXX` (backend) and `YYYY` (frontend) ports.

2. **Backend Generation Prompt**
   - Must include all specified backend features.
   - Must list required pip dependencies in form of requirements.txt.


3. **Frontend Generation Prompt**
   - Must include all specified frontend features.
   - Must list required npm dependencies in form of package.json (and vite.config.js if necessary)


**Very important:** Your app should be feature rich and production ready.
```