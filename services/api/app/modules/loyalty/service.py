# app/modules/loyalty/service.py
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.modules.loyalty import repository
from app.modules.loyalty.models import BonusAccount, TransactionType


async def open_account(session: AsyncSession, user_id: uuid.UUID) -> BonusAccount:
    """Открывает бонусный счёт на начальном уровне в текущей транзакции, не коммитит."""
    level = await repository.get_entry_level(session, datetime.now(UTC))
    if level is None:
        raise ApiError(500, "LOYALTY_LEVEL_NOT_CONFIGURED", "Не настроен начальный уровень")
    account = BonusAccount(user_id=user_id, level_id=level.id, balance=0, accumulated_total=0)
    repository.add_account(session, account)
    await session.flush()
    return account


async def get_purchase_rewards(
    session: AsyncSession,
    purchase_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[int, int]:
    """Возвращает количество списанных баллов и начисленный кешбэк по покупке."""
    transactions = await repository.get_purchase_transactions(
        session,
        purchase_id,
        user_id,
    )

    points_redeemed = abs(
        sum(
            transaction.amount
            for transaction in transactions
            if transaction.type == TransactionType.REDEMPTION
        )
    )

    cashback_earned = sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == TransactionType.ACCRUAL
    )

    return points_redeemed, cashback_earned
