FROM denoland/deno
# Set working directory
WORKDIR /app

# Install Node.js and npm
# Combine commands to reduce layers and leverage caching
ENV NODE_VERSION=18.x
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_$NODE_VERSION | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy package.json and lock file (if available) first for caching dependencies
COPY package.json package-lock.json* ./

# Install dependencies with detailed logging
RUN npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy remaining application files
COPY vite.config.js .
COPY index.html .
COPY src src/

# Expose the application port
EXPOSE 5646
ENV PORT=5646

# Start the development server
CMD ["npm", "run", "dev"]
