from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    User registration endpoint.

    :param body: User data for registration.
    :type body: UserModel
    :param background_tasks: Background tasks for sending email.
    :type background_tasks: BackgroundTasks
    :param request: The HTTP request object.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the user already exists or if there is an error during registration.
    :return: A response containing the newly created user and a success message.
    :rtype: UserResponse
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return {
        "user": new_user,
        "detail": "User successfully created. Check your email for confirmation.",
    }


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenModel:
    """
    User login endpoint.

    :param body: OAuth2 password request form containing username and password.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the user does not exist, email is not confirmed, or password is invalid.
    :return: A response containing access and refresh tokens.
    :rtype: TokenModel
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
)-> TokenModel:
    """
    Refresh access token endpoint.

    :param credentials: HTTP authorization credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the refresh token is invalid or does not match the user's stored token.
    :return: A response containing a new access token and refresh token.
    :rtype: TokenModel
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Confirm user's email using a token.

    :param token: The token sent to the user's email for confirmation.
    :type token: str
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the token is invalid or if the user does not exist.
    :return: A message indicating the result of the email confirmation.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Request email confirmation for a user.

    :param body: RequestEmail object containing the user's email.
    :type body: RequestEmail
    :param background_tasks: Background tasks for sending email.
    :type background_tasks: BackgroundTasks
    :param request: The HTTP request object.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :raises HTTPException: If the user does not exist or if the email is already confirmed.
    :return: A message indicating the result of the email request.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    elif user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for confirmation."}
