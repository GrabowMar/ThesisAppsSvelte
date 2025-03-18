FROM node:18

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Single install command for all dependencies
RUN npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy the rest of the app
COPY vite.config.js .
COPY index.html .
COPY src/ src/

# Expose the application port (make sure Vite is configured to bind to 0.0.0.0)
EXPOSE 5995
ENV PORT=5995

# Start the React development server
CMD ["npx", "vite", "--host", "0.0.0.0"]
