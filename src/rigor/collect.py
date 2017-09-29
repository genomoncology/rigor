import asyncio
import aiofiles
import glob
import os

from . import get_logger


def collect(suite):
    log = get_logger()
    log.info("collecting tests", paths=suite.paths, cwd=os.getcwd())

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(async_collect(suite))
    loop.run_until_complete(future)

    for case in future.result():
        suite.add_case(case)

    log.info("tests collected", queued=len(suite.queued),
             skipped=len(suite.skipped))


async def async_collect(suite):
    tasks = []
    for pattern in glob_patterns(suite):
        for file_path in glob.iglob(pattern, recursive=True):
            tasks.append(asyncio.ensure_future(collect_case(suite, file_path)))
    cases = await asyncio.gather(*tasks)
    return cases


async def collect_case(suite, file_path):
    from . import Case
    async with aiofiles.open(file_path, mode='r') as f:
        return Case.loads(await f.read(), file_path=file_path)


def glob_patterns(suite):
    for path in suite.paths or ['.']:
        if os.path.exists(path) and os.path.isfile(path):
            yield path

        for file_prefix in suite.prefixes or ['']:
            for extension in suite.extensions or ['rigor']:
                file_pattern = "%s*.%s" % (file_prefix, extension)
                yield os.path.join(path, "**", file_pattern)
