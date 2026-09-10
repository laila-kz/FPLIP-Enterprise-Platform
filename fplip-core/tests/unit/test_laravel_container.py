"""
Unit tests for Laravel containerization and Docker Compose integration.
"""

from pathlib import Path
import yaml
import pytest


def test_laravel_dockerfile_exists_and_valid():
    """Verify that fplip-investigate/Dockerfile is configured properly."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    dockerfile_path = repo_root / "fplip-investigate" / "Dockerfile"
    assert dockerfile_path.exists(), f"Laravel Dockerfile not found at {dockerfile_path}"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM php:8.2-cli" in content
    assert "pdo_sqlite" in content
    assert "EXPOSE 8081" in content
    assert 'CMD ["php", "artisan", "serve"' in content


def test_laravel_dockerignore_exists():
    """Verify that .dockerignore excludes temporary and environment files."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    dockerignore_path = repo_root / "fplip-investigate" / ".dockerignore"
    assert dockerignore_path.exists()

    content = dockerignore_path.read_text(encoding="utf-8")
    assert ".env" in content
    assert "vendor" in content
    assert "node_modules" in content


def test_docker_compose_laravel_service():
    """Verify that docker-compose.yml defines laravel service with persistent volume mounts."""
    compose_path = Path(__file__).resolve().parent.parent.parent / "docker-compose.yml"
    assert compose_path.exists()

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    assert "laravel" in services, "Missing laravel service in docker-compose.yml"

    laravel_svc = services["laravel"]
    assert laravel_svc["container_name"] == "fplip-investigate"
    assert any("8081" in p for p in laravel_svc["ports"])
    
    # Verify database volume persistence mount
    volumes = laravel_svc.get("volumes", [])
    assert any("database" in v for v in volumes), "Missing persistent database volume mount"
    assert any("storage" in v for v in volumes), "Missing persistent storage volume mount"
