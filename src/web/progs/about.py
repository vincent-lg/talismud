from data.base import db

async def get(page):
    """GET /about."""
    page.rooms = db.Room.select().count()
