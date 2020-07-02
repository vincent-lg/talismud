from aiohttp import web
from aiohttp_session import get_session

from data.base import db

async def post(request):
    data = await request.post()
    session = await get_session(request)

    # Get the corresponding username, if possible
    username = data.get("username", "")
    account = db.Account.get(username=username)

    if account:
        # Check the password
        password = data.get("password", "")
        if account.is_correct_password(password):
            session["account"] = account
            raise web.HTTPFound('/')

async def get(request):
    session = await get_session(request)
    print(f"this request is logged in as: {session.get('account', None)}")
