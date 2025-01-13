
FROM denoland/deno:1.37.1

WORKDIR /app

# Install Node.js and npm
ENV NODE_VERSION=18.x
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_$NODE_VERSION | bash -
RUN apt-get install -y nodejs

# Copy package files
COPY package.json .
COPY vite.config.js .
COPY index.html .

# Install dependencies with detailed logging
RUN set -x && \
    npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
    find node_modules/ -type f | wc -l

# Copy source files
COPY src src/

EXPOSE 5685
ENV PORT=5685

# Start the development server
CMD ["npm", "run", "dev"]
