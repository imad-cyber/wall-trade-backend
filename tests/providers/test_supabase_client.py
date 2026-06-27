"""Supabase provider tests."""
from unittest.mock import MagicMock, patch

from app.providers.supabase.client import close_supabase_client, get_supabase_client


def test_get_supabase_client_singleton():
    close_supabase_client()
    with patch("app.providers.supabase.client.create_client") as mock_create:
        mock_create.return_value = MagicMock()
        client1 = get_supabase_client()
        client2 = get_supabase_client()
        assert client1 is client2
        mock_create.assert_called_once()
    close_supabase_client()
