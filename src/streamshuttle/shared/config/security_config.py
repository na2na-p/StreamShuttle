"""Security Configuration"""

from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """Security Configuration

    Provides security measures for public usage.
    """

    max_url_length: int = Field(
        default=2000,
        description="""Maximum URL length limit (default: 2000 characters)

        As a security measure for public usage, rejects abnormally long URLs.
        YouTube URLs are typically under 200 characters, but considering query parameters,
        the limit is set to 2000 characters.

        This limit prevents the following attacks:
        - DoS attacks (resource consumption from processing extremely long URLs)
        - Buffer overflow attacks
        - Log file bloat attacks
        """,
    )
    csrf_secret_key: str = Field(
        description=(
            "Secret key for CSRF protection "
            "(environment variable: SECURITY_CSRF_SECRET_KEY)"
        ),
    )
    csrf_token_expiry_seconds: int = Field(
        default=600,
        description=(
            "CSRF token expiry time in seconds (default: 600 seconds = 10 minutes)"
        ),
    )

    model_config = {
        "env_prefix": "SECURITY_",
        "frozen": True,
    }

    @model_validator(mode="before")
    @classmethod
    def validate_csrf_secret_key(cls, data: Any) -> Any:
        """Validate CSRF secret key existence and customize error message"""
        if isinstance(data, dict) and "csrf_secret_key" not in data:
            error_message = (
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "ERROR: CSRF secret key (SECURITY_CSRF_SECRET_KEY) is not set\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "\n"
                "For security reasons, setting the CSRF secret key is required.\n"
                "\n"
                "Setup instructions:\n"
                "  1. Create .env file:\n"
                "     $ cp .env.example .env\n"
                "\n"
                "  2. Generate CSRF secret key:\n"
                '     $ python -c "import secrets; print(secrets.token_hex(32))"\n'
                "\n"
                "  3. Set in .env file:\n"
                "     SECURITY_CSRF_SECRET_KEY=<generated_value>\n"
                "\n"
                "  4. Restart the application\n"
                "\n"
                "For details, refer to the 'Environment Variables' section in README.md.\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            raise ValueError(error_message)
        return data
