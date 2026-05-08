FROM datajoint/nginx:v0.0.16

# Download and extract to /usr/share/nginx/html (matching original compose)
RUN rm -rf /usr/share/nginx/html && \
    curl -L https://github.com/datajoint/datajoint-labbook/releases/download/0.1.1/static-djlabbook-0.1.1.zip \
    -o /tmp/static.zip && \
    unzip /tmp/static.zip -d /usr/share/nginx && \
    mv /usr/share/nginx/build /usr/share/nginx/html && \
    rm /tmp/static.zip && \
    ls -la /usr/share/nginx/html/