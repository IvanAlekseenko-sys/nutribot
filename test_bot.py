import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from time import time
from collections import defaultdict
import os


os.environ.setdefault("TELEGRAM_TOKEN", "test_token")
os.environ.setdefault("GEMINI_API_KEY", "test_key")


@pytest.fixture(autouse=True)
def reset_rate_limit():
    import importlib
    import bot
    importlib.reload(bot)
    bot.user_last_request = defaultdict(float)
    yield
    bot.user_last_request = defaultdict(float)


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 12345
    update.message = MagicMock()
    update.message.text = ""
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock()


class TestCheckRateLimit:
    def test_first_request_allowed(self):
        from bot import check_rate_limit
        assert check_rate_limit(1) is True

    def test_second_request_blocked(self):
        from bot import check_rate_limit
        check_rate_limit(1)
        assert check_rate_limit(1) is False

    def test_different_users_independent(self):
        from bot import check_rate_limit
        check_rate_limit(1)
        assert check_rate_limit(2) is True

    def test_request_after_delay_allowed(self):
        from bot import check_rate_limit, RATE_LIMIT_SECONDS
        check_rate_limit(1)
        import bot
        bot.user_last_request[1] = time() - RATE_LIMIT_SECONDS - 1
        assert check_rate_limit(1) is True


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_empty_message(self, mock_update, mock_context):
        mock_update.message.text = ""
        from bot import handle_message
        await handle_message(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "❌ Пустое сообщение / Empty message"
        )

    @pytest.mark.asyncio
    async def test_too_long_message(self, mock_update, mock_context):
        mock_update.message.text = "а" * 501
        from bot import handle_message
        await handle_message(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Слишком длинное" in call_text or "too long" in call_text.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_blocks(self, mock_update, mock_context):
        mock_update.message.text = "курица"
        from bot import handle_message, check_rate_limit
        check_rate_limit(12345)
        await handle_message(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Подожди" in call_text or "Wait" in call_text

    @pytest.mark.asyncio
    @patch("bot.client")
    async def test_valid_request_calls_api(self, mock_client, mock_update, mock_context):
        mock_update.message.text = "гречка"
        mock_response = MagicMock()
        mock_response.text = "🍽 Гречка\n🔥 343 kcal\n💪 13g\n🧈 6g\n🍞 72g"
        mock_client.models.generate_content.return_value = mock_response

        from bot import handle_message
        await handle_message(mock_update, mock_context)

        assert mock_update.message.reply_text.call_count == 2
        first_call = mock_update.message.reply_text.call_args_list[0][0][0]
        assert "Считаю" in first_call or "Calculating" in first_call

    @pytest.mark.asyncio
    @patch("bot.client")
    async def test_api_429_error(self, mock_client, mock_update, mock_context):
        mock_update.message.text = "курица"
        mock_client.models.generate_content.side_effect = Exception("Error 429: rate limit")

        from bot import handle_message
        await handle_message(mock_update, mock_context)

        call_text = mock_update.message.reply_text.call_args_list[1][0][0]
        assert "много запросов" in call_text or "Too many" in call_text

    @pytest.mark.asyncio
    @patch("bot.client")
    async def test_api_key_error(self, mock_client, mock_update, mock_context):
        mock_update.message.text = "курица"
        mock_client.models.generate_content.side_effect = Exception("API_KEY_INVALID")

        from bot import handle_message
        await handle_message(mock_update, mock_context)

        call_text = mock_update.message.reply_text.call_args_list[1][0][0]
        assert "API ключа" in call_text or "API key" in call_text

    @pytest.mark.asyncio
    @patch("bot.client")
    async def test_service_unavailable(self, mock_client, mock_update, mock_context):
        mock_update.message.text = "курица"
        mock_client.models.generate_content.side_effect = Exception("Error 503 UNAVAILABLE")

        from bot import handle_message
        await handle_message(mock_update, mock_context)

        call_text = mock_update.message.reply_text.call_args_list[1][0][0]
        assert "недоступен" in call_text or "unavailable" in call_text.lower()

    @pytest.mark.asyncio
    @patch("bot.client")
    async def test_long_response_truncated(self, mock_client, mock_update, mock_context):
        mock_update.message.text = "гречка"
        mock_response = MagicMock()
        mock_response.text = "x" * 4100
        mock_client.models.generate_content.return_value = mock_response

        from bot import handle_message
        await handle_message(mock_update, mock_context)

        call_text = mock_update.message.reply_text.call_args_list[1][0][0]
        assert "обрезан" in call_text or "truncated" in call_text.lower()


class TestStartCommand:
    @pytest.mark.asyncio
    async def test_start_replies(self, mock_update, mock_context):
        from bot import start
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Привет" in call_text or "Hi" in call_text


class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_replies(self, mock_update, mock_context):
        from bot import help_command
        await help_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "пользоваться" in call_text or "How to use" in call_text
