# Use the official Node.js image as the base
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker caching
COPY package.json package-lock.json* ./

# Install dependencies with detailed logging
RUN npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy the remaining application files (adjust file names/paths as needed for your project)
COPY vite.config.js .
COPY index.html .
COPY src src/

# Expose the application port (adjust the port if needed)
EXPOSE 5923
ENV PORT=5923


# Start the React development server
CMD ["npm", "run", "dev"]
