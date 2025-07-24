import logging
from aiogram import Bot

logger = logging.getLogger(__name__)


# Проверка, подписан ли пользователь на канал/группу (Важно! Бот должен быть админом канала)
async def check_subscription_by_username(bot: Bot, user_id: int, channel_username: str) -> bool:
    try:
        # Получаем ID канала по channel_username
        chat = await bot.get_chat(channel_username)
        channel_id = chat.id
        logger.debug(f"ID канала по username {channel_username}: {channel_id}")

        # Используем ID канала для проверки подписки
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.error(f"Ошибка проверки подписки пользователя {user_id}: {e}")
        return False
