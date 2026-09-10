"""
Unit test verifying Nginx reverse proxy configuration syntax and routing structure.
"""

from pathlib import Path
import pytest


def test_nginx_conf_exists_and_valid():
    """Verify that proxy/nginx.conf exists and defines all required route locations."""
    nginx_conf_path = Path(__file__).resolve().parent.parent.parent / "proxy" / "nginx.conf"
    assert nginx_conf_path.exists(), f"Nginx config file not found at {nginx_conf_path}"

    content = nginx_conf_path.read_text(encoding="utf-8")

    # Verify key proxy routes exist
    assert "location /api/" in content, "Missing /api/ proxy route"
    assert "location /airflow/" in content, "Missing /airflow/ proxy route"
    assert "location /app/" in content, "Missing /app/ proxy route"
    assert "location /bi/" in content, "Missing /bi/ proxy route"
    assert "location /health" in content, "Missing /health endpoint"

    # Verify upstream endpoints
    assert "proxy_pass http://api:8000/;" in content
    assert "proxy_pass http://airflow-webserver:8080/;" in content
    assert "proxy_pass http://laravel:8081/;" in content or "proxy_pass http://host.docker.internal:8081/;" in content
    assert "proxy_pass http://host.docker.internal:8088/;" in content

    # Verify TLS / SSL Termination settings
    assert "listen 8443 ssl;" in content, "Missing listen 8443 ssl directive"
    assert "ssl_certificate /etc/nginx/certs/cert.pem;" in content, "Missing ssl_certificate directive"
    assert "ssl_certificate_key /etc/nginx/certs/key.pem;" in content, "Missing ssl_certificate_key directive"


def test_tls_certs_exist():
    """Verify that TLS cert.pem and key.pem are generated and present in proxy/certs/."""
    certs_dir = Path(__file__).resolve().parent.parent.parent / "proxy" / "certs"
    cert_file = certs_dir / "cert.pem"
    key_file = certs_dir / "key.pem"

    assert cert_file.exists(), f"Certificate file missing at {cert_file}"
    assert key_file.exists(), f"Private key file missing at {key_file}"
    assert cert_file.stat().st_size > 0
    assert key_file.stat().st_size > 0

