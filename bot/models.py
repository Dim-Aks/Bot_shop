from sqlalchemy import Integer, String, Boolean, ForeignKey, Numeric, Identity
from sqlalchemy.orm import relationship, Mapped, mapped_column

from models_base import Base


class Cart(Base):
    __tablename__ = "cart_cart"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users_user.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products_product.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="cart")
    product: Mapped["Product"] = relationship(back_populates="cart")

    def __str__(self):
        return f'Корзина пользователя:{self.user_id}, Продукт: {self.product_id}, Количество: {self.quantity}'

    def __repr__(self):
        return (f"Корзина(id={self.id}, пользователь={self.user_id}, product_id={self.product_id},"
                f" Количество={self.quantity}, Цена={self.price})")


class Category(Base):
    __tablename__ = "products_category"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Связи
    subcategory: Mapped[list["SubCategory"]] = relationship(back_populates="category")
    product: Mapped[list["Product"]] = relationship(back_populates="category")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Категория (id={self.id}, name={self.name})"


class Product(Base):
    __tablename__ = "products_product"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("products_category.id"), nullable=False)
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("products_subcategory.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    photo: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    # Связи
    category: Mapped["Category"] = relationship(back_populates="product")
    subcategory: Mapped["SubCategory"] = relationship(back_populates="product")
    cart: Mapped[list["Cart"]] = relationship(back_populates="product")

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f"Продукт (id={self.id}, category_id={self.category_id}, subcategory_id={self.subcategory_id},"
                f" name={self.name}, photo={self.photo}, price={self.price})")


class SubCategory(Base):
    __tablename__ = "products_subcategory"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("products_category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    # Связи
    category: Mapped["Category"] = relationship(back_populates="subcategory")
    product: Mapped[list["Product"]] = relationship(back_populates="subcategory")

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f"Подкатегория (id={self.id}, category_id={self.category_id},"
                f" name={self.name}, description={self.description})")


class User(Base):
    __tablename__ = "users_user"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(String(100), unique=False, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    cart: Mapped[list["Cart"]] = relationship(back_populates="user")

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.user_id})"

    def __repr__(self):
        return (f"Пользователь (id={self.id}, user_id={self.user_id}, username={self.username},"
                f" first_name={self.first_name}, last_name={self.last_name}, is_active={self.is_active})")
