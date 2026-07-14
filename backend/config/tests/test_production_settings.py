import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_django_deploy_check_with_production_env() -> None:
    env = os.environ.copy()
    env.update(
        {
            "DEBUG": "False",
            "ALLOWED_HOSTS": "example.com,www.example.com",
            "SECRET_KEY": "test-deploy-check-secret-key-min-50-chars-long-enough",
            "POSTGRES_DB": "ci",
            "POSTGRES_USER": "ci",
            "POSTGRES_PASSWORD": "ci",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
        }
    )
    result = subprocess.run(
        [sys.executable, "backend/manage.py", "check", "--deploy"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
