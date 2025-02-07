```markdown
# Wiki Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a wiki system.
2. Keep ALL changes within **app.py** and **App.svelte** files only.
3. Do NOT modify the project structure.
4. Do NOT create additional files unless explicitly requested.
5. Include core wiki features.
6. Focus on content management essentials.
7. **Note:** Multipage routing is possible in both the backend and frontend. In **app.py**, you can define multiple routes to handle different pages or API endpoints. In **App.svelte**, client-side routing can be implemented using conditional rendering or a routing library.

## Project Description

**Wiki System**  
A wiki platform built with Flask and Svelte, featuring page management and content organization.

**Key Features:**

- Page creation/editing
- Content organization
- Search functionality
- Version history
- Simple formatting

**Technical Stack:**

- **Backend:** Flask with SQLAlchemy
- **Frontend:** Svelte with markdown support
- **Additional:** Content versioning

## Technical Requirements Analysis

### Backend Requirements
1. **Core Features:**
   - Page management
   - Content versioning
   - Search functionality
   - Link handling

2. **Integration Requirements:**
   - Database setup
   - Content storage
   - Version control

### Frontend Requirements
1. **Visual Elements:**
   - Page editor
   - Content view
   - Search interface
   - History display
   - Navigation menu

2. **Functional Elements:**
   - Content editing
   - Page navigation
   - Search handling
   - Version control

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
  // Implement client-side routing here using conditional rendering
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

**Note:** Backend implementation must be confirmed before proceeding with frontend generation.
```