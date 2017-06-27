rigor
=====

- Functional API Testing Framework
- Built with Python 3.6
- Multiple Purposes: Document API, Test API, Smoke/Functional/TDD, etc.
- Asynchronous (ayncio) collection (aiofiles) and execution (aiohttp)
- Cucumber-inspired Given/When/Then approach to test cases.
- Different from Cucumber because it is imperative. Tied explicitly to the
  API not the user stories.
- Declarative syntax using YAML test case descriptions
- Uses Jmespath for data extraction and less-brittle validation
- `status` expects a 2XX by default, but can be overridden in step request.
- `rigor` descends directories using file prefix and extensions
  (default `yml` and `yaml`).
- `tags` can be included (e.g. smoke) or excluded (e.g. broken).
- Asynchronous mode can be disabled by specifying `concurrency=1`
- Namespace __uuid__ for uniquely naming things in case of concurrency.
- Rendering using [mako: http://www.makotemplates.org/]
- Command-line with [click: http://click.pocoo.org/]


Setup
-----

```bash
$ pip install rigor
$ cd /path/to/directory/containing/tree/of/rigor/yamls/
$ rigor
```
