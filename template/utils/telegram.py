import aiohttp
import loguru


class TelegramLogger:
    def __init__(self, bot_token: str, user_id: int) -> None:
        self.bot_token = bot_token

        self.data={
            "chat_id": int(user_id), 
            "parse_mode": "html", 
            "disable_web_page_preview": True
        }

    async def send_message(self, message_text: str) -> None:
        try:
            self.data["text"] = message_text

            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.post(
                    f"http://api.telegram.org/bot{self.bot_token}/sendMessage", data=self.data
                ) as response:
                    if response.status == 200:
                        loguru.logger.success(f'Message was sent to: {self.data["chat_id"]}')
                    
                    else:
                        text = await response.text()
                        raise Exception(f'Bad status code: {response.status} | text: {text}')

        except Exception as _err:
            loguru.logger.error(f'Failed send message with data: {self.data} | error: {_err}')
            