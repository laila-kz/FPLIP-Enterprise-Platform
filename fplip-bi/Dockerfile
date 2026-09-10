FROM apache/superset:4.1.1

USER root

# Install BigQuery drivers and Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy custom Superset configuration
COPY superset_config.py /app/pythonpath/superset_config.py

# Copy custom entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Ensure superset_home exists and is writable
RUN mkdir -p /app/superset_home && chown -R superset:superset /app/superset_home /app/pythonpath

USER superset

ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py \
    PYTHONPATH=/app/pythonpath \
    FLASK_APP=superset.app:create_app()

EXPOSE 8088

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
