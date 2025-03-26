FROM node:18

WORKDIR /app

# Copy package files
COPY package.json ./

# Optimized install command that doesn't require package-lock.json
RUN npm install --prefer-offline --no-audit --no-progress && \
    npm ls --prod && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy the rest of the app
COPY . .
# Expose the application port (make sure Vite is configured to bind to 0.0.0.0)
EXPOSE 5923
ENV PORT=5923

# Start the React development server
CMD ["npx", "vite", "--host", "0.0.0.0"]
