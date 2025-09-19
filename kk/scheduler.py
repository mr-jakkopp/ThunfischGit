import asyncio
import datetime as dt
from kk.utils import now

async def wait_until_hour(hour: int, minute: int = 0) -> None:
    now_ = now()
    target = now_.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now_:
        target += dt.timedelta(days=1)
    print("Sleeping for ", (target - now_).total_seconds() / 60, "minutes.")
    await asyncio.sleep((target - now_).total_seconds())

async def sleep_until_next_full_hour() -> None:
    now_ = now()
    target = (now_ + dt.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    await asyncio.sleep((target - now_).total_seconds())


async def sleep_for_hours(hours: int) -> None:
    now_ = now()
    target = (now_ + dt.timedelta(hours=hours)).replace(minute=0, second=0, microsecond=0)
    await asyncio.sleep((target - now_).total_seconds())