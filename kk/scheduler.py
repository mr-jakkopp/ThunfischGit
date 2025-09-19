import asyncio
import datetime as dt

async def wait_until_hour(hour: int, minute: int = 0) -> None:
    now = dt.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    print("Sleeping for ", (target - now).total_seconds() / 60, "minutes.")
    await asyncio.sleep((target - now).total_seconds())

async def sleep_until_next_full_hour() -> None:
    now = dt.datetime.now()
    target = (now + dt.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    await asyncio.sleep((target - now).total_seconds())


async def sleep_for_hours(hours: int) -> None:
    now = dt.datetime.now()
    target = (now + dt.timedelta(hours=hours)).replace(minute=0, second=0, microsecond=0)
    await asyncio.sleep((target - now).total_seconds())