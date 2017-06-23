rigor
=====

- Functional API Testing Framework
- Built with Python 3.6
- Asynchronous (ayncio) collection (aiofiles) and execution (aiohttp)
- Cucumber-inspired Given/When/Then approach to test cases
- Declarative syntax using YAML test case descriptions
- Uses Jmespath for data extraction and less-brittle validation
- `status` expects a 2XX by default, but can be overridden in step request.
- `rigor` descends directories using file prefix and extensions
  (default `yml` and `yaml`).
- `tags` can be included (e.g. smoke) or excluded (e.g. broken).
- Asynchronous mode can be disabled by specifying `concurrency=1`
- 


Setup
-----

```bash
$ pip install rigor
$ cd /path/to/directory/containing/tree/of/rigor/yamls/
$ rigor
```
