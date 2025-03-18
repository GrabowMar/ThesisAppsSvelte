# Use the official Node.js image as the base
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker caching
COPY package.json package-lock.json* ./

# Copy package.json and package-lock.json first to leverage Docker caching
RUN npm install --save-dev vite@latest @vitejs/plugin-react

# Install dependencies with detailed logging
RUN npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy the remaining application files
COPY vite.config.js .
COPY index.html .
COPY src/ src/

# Expose the application port (make sure Vite is configured to bind to 0.0.0.0)
EXPOSE 5783
ENV PORT=5783

# Start the React development server
CMD ["npx", "vite", "--host", "0.0.0.0"]
