from aiohttp import web

from data.base import db

async def post(request, session):
    data = await request.post()

    # Get the corresponding username, if possible
    username = data.get("username", "")
    account = db.Account.get(username=username)

    if account:
        # Check the password
        password = data.get("password", "")
        if account.is_correct_password(password):
            session["account"] = account
            raise web.HTTPFound('/')

async def get(session):
    print(f"this request is logged in as: {session.get('account', None)}")
