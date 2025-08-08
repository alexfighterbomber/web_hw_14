from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.engine import Result

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    '''
    Retrieves a user from the database by their email address.

    :param email: The email address of the user to retrieve.
    :type email: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The user object if found, otherwise None.
    :rtype: User | None
    '''
    stmt = select(User).where(User.email == email)
    result: Result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession) -> User:
    """
    Creates a new user in the database.
    
    :param body: The user data to create.
    :type body: UserModel
    :param db: The database session.
    :type db: AsyncSession
    :return: The newly created user.
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    
    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """
    Updates the user's refresh token in the database.

    :param user: The user to update.
    :type user: User
    :param token: The new refresh token to set, or None to clear it.
    :type token: str | None
    :param db: The database session.
    :type db: AsyncSession
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Marks the user's email as confirmed in the database.

    :param email: The email of the user to confirm.
    :type email: str
    :param db: The database session.
    :type db: AsyncSession
    """
    stmt = update(User).where(User.email == email).values(confirmed=True)
    await db.execute(stmt)
    await db.commit()


async def update_avatar(email: str, url: str, db: AsyncSession) -> User:
    """
    Updates the user's avatar URL in the database.

    :param email: The email of the user whose avatar is to be updated.
    :type email: str
    :param url: The new avatar URL to set.
    :type url: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The user with the updated avatar.
    :rtype: User
    """
    stmt = select(User).where(User.email == email)
    result: Result = await db.execute(stmt)
    user = result.scalar_one()
    
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user