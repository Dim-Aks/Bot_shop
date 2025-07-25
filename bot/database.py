import logging
import os
from typing import Any, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload

from models import Cart, Category, Product, SubCategory, User


logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(async_engine, class_=AsyncSession)


async def get_async_db():
    async_session = async_session_maker()
    async with async_session as session:
        try:
            yield session
        finally:
            await session.close()


# Получает пользователя по user_id (Telegram ID)
async def get_user_tg_id(tg_id: int) -> User | None:
    async for db in get_async_db():
        try:
            stmt = select(User).where(User.user_id == tg_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя с user_id {tg_id}: {e}")
            return None


# Добавляет пользователя в таблицу user, если его там еще нет (или обновляет)
async def add_user_if_not_exists(user_id: int, username: str, first_name: str, last_name: str) -> User | None:
    async for db in get_async_db():
        try:
            # Пытаемся получить пользователя по user_id
            user = await get_user_tg_id(user_id)

            if user:
                logger.info(f"Пользователь (ID: {user_id}) уже существует.")
                if user.username != username or user.first_name != first_name or user.last_name != last_name:
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    await db.commit()
                    await db.refresh(user)
                    logger.info(f"Обновлен существующий пользователь: {user}")
                return user
            else:
                new_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                logger.info(f"Добавлен новый пользователь: {new_user}")
                return new_user
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка добавления пользователя (ID: {user_id}): {e}")
            return None


# Получаем список категорий
async def fetch_categories() -> Sequence[Category] | list[Any]:
    async for db in get_async_db():
        try:
            stmt = select(Category)
            result = await db.execute(stmt)
            categories = result.scalars().all()
            logger.info(f"Получены категории: {str(categories)}")
            return categories
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []


# Получаем список подкатегорий для заданной категории
async def fetch_subcategories(category_id: int) -> Sequence[SubCategory] | list[Any]:
    async for db in get_async_db():
        try:
            stmt = select(SubCategory).where(SubCategory.category_id == category_id)
            result = await db.execute(stmt)
            subcategories = result.scalars().all()
            logger.info(f"Получены подкатегории: {subcategories}")
            return subcategories
        except Exception as e:
            logger.error(f"Ошибка получения подкатегорий: {e}")
            return []


# Получаем объект подкатегории
async def fetch_subcategory(subcategory_id: int) -> SubCategory | None:
    async for db in get_async_db():
        try:
            stmt = select(SubCategory).where(SubCategory.id == subcategory_id)
            result = await db.execute(stmt)
            subcategory = result.scalar_one_or_none()
            return subcategory
        except Exception as e:
            logger.error(f"Ошибка получения подкатегории: {e}")
            return None


# Получаем список товаров для заданной подкатегории
async def fetch_products_by_subcategory(subcategory_id: int) -> Sequence[Product] | list[Any]:
    async for db in get_async_db():
        try:
            stmt = select(Product).where(Product.subcategory_id == subcategory_id)
            result = await db.execute(stmt)
            products = result.scalars().all()
            logger.info(f"Получены товары: {list(products)}")
            return products
        except Exception as e:
            logger.error(f"Ошибка получения товаров: {e}")
            return []


# Получаем информацию о продукте
async def fetch_product(product_id: int) -> Product | None:
    async for db in get_async_db():
        try:
            stmt = select(Product).where(Product.id == product_id)
            result = await db.execute(stmt)
            product = result.scalar_one_or_none()
            logger.info(f"Получена информация о продукте: {product}")
            return product
        except Exception as e:
            logger.error(f"Ошибка получения товара: {e}")
            return None


# Добавляем товар в корзину пользователя
async def add_to_cart(user_id: int, product_id: int, quantity: float | int) -> bool:
    async for db in get_async_db():
        try:
            # получение пользователя из базы данных
            user = await get_user_tg_id(user_id)

            if not user:
                logger.error(f"Пользователь с ID {user.id} не найден.")
                return False

            logger.info(f"Найден пользователь: {user} c id {user.id}")

            # получение товара из базы данных
            product = await fetch_product(product_id)

            if not product:
                logger.error(f"Товар с ID {product_id} не найден.")
                return False

            stmt = select(Cart).where(Cart.user_id == user.id, Cart.product_id == product_id)
            result = await db.execute(stmt)
            cart_item = result.scalar_one_or_none()
            logger.info(f"Чекаем есть ли уже корзина с этим товаром у этого пользователя либо None ({cart_item})")

            if cart_item:
                # Товар уже есть в корзине, обновляем количество
                cart_item.quantity += quantity
                logger.info(
                    f"Обновлено количество товара в корзине (ID: {cart_item.id}), quantity: {cart_item.quantity}"
                )
            else:
                logger.info(f"Товара нет в корзине, данные для добавления({user.id, product_id, quantity, product.price})")
                # Товара нет в корзине, создаем новый элемент
                new_cart_item = Cart(
                    user_id=user.id,
                    product_id=product_id,
                    quantity=quantity,
                    price=product.price,
                )
                logger.info(f"Подготовлен новый товар для добавления в корзину ({new_cart_item})")
                db.add(new_cart_item)
                logger.info(f"Добавлен новый товар в сессию ({new_cart_item})")
            await db.commit()  # Один commit для всех изменений в этой сессии
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка добавления товара в корзину: {e}")
            return False


# Получаем корзину пользователя
async def fetch_cart(user_id: int) -> list[dict]:
    async for db in get_async_db():
        try:
            user = await get_user_tg_id(user_id)
            stmt = select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.product))
            result = await db.execute(stmt)
            cart_items = result.scalars().all()

            # Формируем список словарей с информацией о товарах
            cart_data = []
            for item in cart_items:
                cart_data.append({
                    'id': item.id,
                    'name': item.product.name,
                    'price': item.product.price,
                    'quantity': item.quantity,
                    'photo': item.product.photo,
                }
                )
            return cart_data
        except Exception as e:
            logger.error(f"Ошибка получения корзины: {e}")
            return []


# Удаляем товар из корзины
async def remove_from_cart(item_id: int) -> bool:
    async for db in get_async_db():
        try:
            stmt = delete(Cart).where(Cart.id == item_id)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка удаления товара из корзины: {e}")
            return False


# Очищаем корзину пользователя
async def clear_cart(user_id: int) -> bool:
    async for db in get_async_db():
        try:
            user = await get_user_tg_id(user_id)
            stmt = delete(Cart).where(Cart.user_id == user.id)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка очистки корзины: {e}")
            return False
