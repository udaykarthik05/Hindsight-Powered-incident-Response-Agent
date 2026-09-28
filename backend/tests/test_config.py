from app.core.config import Settings


def test_settings_defaults() -> None:
    """Test default values of Settings."""
    settings = Settings()
    assert settings.app_name == "Hindsight Incident Response Agent"
    assert settings.app_port == 8000
    assert settings.hindsight_bank_id is not None
    assert settings.hindsight_timeout > 0


def test_settings_custom_overrides() -> None:
    """Test custom configuration parameters."""
    custom = Settings(
        app_name="Custom Incident Agent",
        app_env="production",
        app_port=9090,
        hindsight_base_url="https://api.hindsight.vectorize.io",
        hindsight_api_key="secret-key-123",
        hindsight_bank_id="prod-incidents",
        hindsight_timeout=15.0,
        cors_origins="https://dashboard.example.com,https://ops.example.com",
    )
    assert custom.app_name == "Custom Incident Agent"
    assert custom.app_env == "production"
    assert custom.app_port == 9090
    assert custom.hindsight_base_url == "https://api.hindsight.vectorize.io"
    assert custom.hindsight_api_key == "secret-key-123"
    assert custom.hindsight_bank_id == "prod-incidents"
    assert custom.hindsight_timeout == 15.0
    assert custom.cors_origin_list == [
        "https://dashboard.example.com",
        "https://ops.example.com",
    ]


def test_cors_origin_list_fallback() -> None:
    """Test CORS origins wildcard fallback when empty."""
    settings = Settings(cors_origins="")
    assert settings.cors_origin_list == ["*"]
