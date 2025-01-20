# **Enhanced Login App Template - Flask + Svelte**

## **Instructions for Language Models**

When implementing this template, follow these structured steps to ensure consistency, accuracy, and adherence to best practices.

---

### **1. Initial Setup Prompts**

Before generating the code, prompt the user to provide the following input parameters:

- **Backend Port:** Replace placeholder `XXXX` accordingly.
- **Frontend Port:** Replace placeholder `YYYY` accordingly.

Ensure the provided ports are used consistently across all project files.

---

### **2. Code Generation Guidelines**

Upon user request, generate the complete project files, including:

- **Backend:**
  - `backend/app.py` – Flask application logic.
  - `backend/Dockerfile` – Backend container setup.
  - `backend/requirements.txt` – Python dependencies.
  
- **Frontend:**
  - `frontend/src/App.svelte` – Svelte component for UI.
  - `frontend/src/main.js` – Frontend entry point.
  - `frontend/index.html` – Base HTML template.
  - `frontend/Dockerfile` – Frontend container setup.
  - `frontend/package.json` – Node.js dependencies.
  - `frontend/vite.config.js` – Build configuration.
  - `frontend/deno.json` – Deno configuration for tasks.

#### **Additional Considerations:**
- Ensure **consistency** between backend and frontend ports across all relevant files.
- Adhere strictly to the provided **project structure** without deviation.

---

### **3. Handling User Modifications**

If the user requests changes to the implementation:

- **Modify only specific files**:
  - `app.py` (backend logic).
  - `App.svelte` (frontend component).
- Ensure backend and frontend compatibility is maintained.
- Update dependency files (`requirements.txt` or `package.json`) **only if new features demand additional dependencies.**

---

## **Project Overview**

A minimal authentication system allowing users to register and log in with email and password.

### **Key Features:**

- **Secure User Authentication:**
  - User registration with email verification.
  - Password hashing using industry-standard algorithms.
  - JWT-based authentication for secure sessions.

- **User Interface Features:**
  - Registration and login with email/password.
  - Password visibility toggle.
  - "Remember me" functionality.
  - Responsive design across devices.

- **Security Enhancements:**
  - Input validation and sanitization.
  - Basic rate-limiting for login attempts.

---

## **Dependency Management Guidelines**

Dependency files (`requirements.txt`, `package.json`) should be generated when:

1. **Explicitly requested** by the user.
2. **New features** introduce additional dependencies.
3. **Security updates** require package adjustments.
4. **User inquiries** about dependencies.

---

### **4. Configuration Details**

Ensure the following configurations are applied:

- **Frontend (`vite.config.js`):**
  - Must define the correct `host` and `port` (default: `5501`).
  - Use the Svelte plugin for Vite.
  
- **Backend (`app.py`):**
  - Should run on user-defined backend port (default: `5001`).
  - CORS should be enabled for cross-origin requests.

---

### **5. Deployment Considerations**

When deployment is requested:

- Generate Docker images for both frontend and backend.
- Provide appropriate environment variable configurations.
- Ensure that `docker-compose.yml` orchestrates both services correctly.

---

This updated prompt improves structure, clarity, and specificity, ensuring better guidance for the model in generating the required project files while maintaining flexibility for user modifications. Let me know if you need further refinements.