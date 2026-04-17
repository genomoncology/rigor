import asyncio
import aiofiles
import glob
import os

from . import get_logger


def collect(suite):
    log = get_logger()
    log.info("collecting tests", paths=suite.paths, cwd=os.getcwd())

    cases = asyncio.run(async_collect(suite))

    for case in cases:
        suite.add_case(case)

    log.info(
        "tests collected", queued=len(suite.queued), skipped=len(suite.skipped)
    )


async def async_collect(suite):
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for file_path in glob_paths(suite):
            tasks.append(tg.create_task(collect_case(suite, file_path)))
    return [task.result() for task in tasks]


async def collect_case(suite, file_path):
    from . import Case

    async with aiofiles.open(file_path, mode="r") as f:
        return Case.loads(await f.read(), file_path=file_path)


def glob_paths(suite):
    for pattern in glob_patterns(suite):
        for file_path in glob.iglob(pattern, recursive=True):
            yield file_path


def glob_patterns(suite):
    for path in suite.paths or ["."]:
        if os.path.exists(path) and os.path.isfile(path):
            yield path

        for file_prefix in suite.prefixes or [""]:
            for extension in suite.extensions or ["rigor"]:
                file_pattern = "%s*.%s" % (file_prefix, extension)
                yield os.path.join(path, "**", file_pattern)
