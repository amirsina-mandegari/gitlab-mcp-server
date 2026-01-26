from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitlab_mr_mcp.gitlab_api import _get_connector, get_session


class TestGetConnector:
    def test_returns_none_when_no_proxy_env(self):
        with patch.dict("os.environ", {}, clear=True):
            result = _get_connector()
            assert result is None

    def test_returns_proxy_connector_when_env_set(self):
        mock_connector = MagicMock()
        with patch.dict("os.environ", {"SOCKS_PROXY": "socks5://127.0.0.1:3546"}):
            with patch("aiohttp_socks.ProxyConnector.from_url", return_value=mock_connector) as mock_from_url:
                result = _get_connector()
                assert result is mock_connector
                mock_from_url.assert_called_once_with("socks5://127.0.0.1:3546")


@pytest.mark.asyncio
async def test_get_session_uses_connector():
    mock_connector = MagicMock()
    mock_session = AsyncMock()

    with patch("gitlab_mr_mcp.gitlab_api._get_connector", return_value=mock_connector):
        with patch("gitlab_mr_mcp.gitlab_api.aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None

            async with get_session() as session:
                assert session is mock_session

            mock_session_class.assert_called_once_with(connector=mock_connector)
