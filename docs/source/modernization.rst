.. _modernization:

Helga Modernization Guide
=========================

This document describes the modernization changes made to the Helga chat bot project to bring it up to current Python best practices and tooling standards.


Overview
--------

The modernization effort focuses on:

- Modern Python packaging (PEP 621)
- Updated CI/CD infrastructure (GitHub Actions)
- Modern development tools (ruff, black, mypy)
- Improved Docker practices
- Enhanced security and dependency management


What's New
----------

1. Modern Python Packaging (``pyproject.toml``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Added:** ``pyproject.toml`` - Modern Python project configuration following PEP 621

**Benefits:**

- Single source of truth for project metadata
- Standardized build system configuration
- Integrated tool configurations (black, ruff, mypy, pytest)
- Better dependency management with optional extras

**Key Features:**

.. code-block:: toml

    [project]
    name = "helga"
    version = "2.0.0"
    requires-python = ">=3.8"
    dependencies = [...]

    [project.optional-dependencies]
    dev = [...]  # Development tools
    docs = [...]  # Documentation tools

**Migration Notes:**

- ``setup.py`` is still present for backward compatibility
- All metadata now lives in ``pyproject.toml``
- Use ``pip install -e .[dev]`` to install with dev dependencies


2. GitHub Actions CI/CD
^^^^^^^^^^^^^^^^^^^^^^^^

**Added:**

- ``.github/workflows/ci.yml`` - Main CI pipeline
- ``.github/workflows/release.yml`` - Release automation
- ``.github/dependabot.yml`` - Automated dependency updates

**Replaced:** Travis CI (``.travis.yml`` is now deprecated)

**Features:**

- Multi-version Python testing (3.8-3.13)
- Parallel job execution
- MongoDB service integration
- Code coverage reporting (Codecov)
- Security scanning (Bandit, Safety)
- Documentation building
- Docker image building
- Automated releases to PyPI and GitHub Container Registry

**Benefits:**

- Faster CI/CD execution
- Better integration with GitHub
- Free for open source projects
- More flexible workflow configuration


3. Pre-commit Hooks
^^^^^^^^^^^^^^^^^^^

**Added:** ``.pre-commit-config.yaml``

**Hooks Included:**

- **Black** - Code formatting
- **Ruff** - Fast Python linting (replaces flake8, isort, and more)
- **Mypy** - Type checking
- **Bandit** - Security scanning
- **Safety** - Dependency vulnerability checking
- **General checks** - Trailing whitespace, file endings, YAML/JSON validation

**Setup:**

.. code-block:: bash

    pip install pre-commit
    pre-commit install

**Usage:**

.. code-block:: bash

    # Run on all files
    pre-commit run --all-files

    # Run on staged files (automatic on commit)
    git commit


4. Modern Linting Tools
^^^^^^^^^^^^^^^^^^^^^^^

Ruff (Replaces flake8, isort, pyupgrade, and more)
""""""""""""""""""""""""""""""""""""""""""""""""""

**Why Ruff?**

- 10-100x faster than traditional tools
- Single tool replaces multiple linters
- Written in Rust for performance
- Compatible with existing configurations

**Configuration in ``pyproject.toml``:**

.. code-block:: toml

    [tool.ruff]
    line-length = 100
    target-version = "py38"

    [tool.ruff.lint]
    select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]

**Usage:**

.. code-block:: bash

    # Check code
    ruff check helga

    # Fix issues automatically
    ruff check --fix helga

    # Format code
    ruff format helga

Black (Code Formatter)
""""""""""""""""""""""

**Configuration:**

.. code-block:: toml

    [tool.black]
    line-length = 100
    target-version = ["py38", "py39", "py310", "py311", "py312"]

**Usage:**

.. code-block:: bash

    # Format code
    black helga

    # Check formatting
    black --check helga

Mypy (Type Checker)
"""""""""""""""""""

**Configuration:**

.. code-block:: toml

    [tool.mypy]
    python_version = "3.8"
    check_untyped_defs = true
    ignore_missing_imports = true

**Usage:**

.. code-block:: bash

    mypy helga


5. Enhanced Docker Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Updated:** ``Dockerfile`` with multi-stage builds

**Improvements:**

- Multi-stage build for smaller images (~50% size reduction)
- Non-root user for security
- Health checks
- Better layer caching
- Security labels and metadata
- Platform-specific optimizations

**Added:** ``.dockerignore`` for faster builds

**Updated:** ``docker-compose.yml`` with:

- Version 3.8 syntax
- Health checks for all services
- Named volumes
- Network isolation
- Restart policies
- Better environment variable management

**Usage:**

.. code-block:: bash

    # Build and run
    docker-compose up --build

    # Run in background
    docker-compose up -d

    # View logs
    docker-compose logs -f helga

    # Stop services
    docker-compose down


6. Development Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Added:** ``requirements-dev.txt``

**Includes:**

- Testing tools (pytest, coverage)
- Code quality tools (black, ruff, mypy)
- Build tools (build, twine)
- Documentation tools (sphinx)
- Security tools (bandit, safety)

**Installation:**

.. code-block:: bash

    pip install -r requirements-dev.txt
    # OR
    pip install -e .[dev]


7. Python Version Support
^^^^^^^^^^^^^^^^^^^^^^^^^

**Current Support:** Python 3.8 - 3.13

**Added:** Python 3.13 support in CI/CD

**Consideration:** Python 3.8 support remains available while newer language features are adopted over time.


Migration Guide
---------------

For Contributors
^^^^^^^^^^^^^^^^

1. **Install pre-commit hooks:**

   .. code-block:: bash

       pip install pre-commit
       pre-commit install

2. **Install development dependencies:**

   .. code-block:: bash

       pip install -e .[dev]

3. **Run tests:**

   .. code-block:: bash

       pytest

4. **Check code quality:**

   .. code-block:: bash

       ruff check helga
       black --check helga
       mypy helga

5. **Format code:**

   .. code-block:: bash

       black helga
       ruff check --fix helga

For Maintainers
^^^^^^^^^^^^^^^

1. **Update GitHub repository settings:**
   - Enable GitHub Actions
   - Configure branch protection rules
   - Set up Codecov integration (optional)
   - Configure PyPI trusted publishing (for releases)

2. **Remove Travis CI:**
   - Disable Travis CI integration
   - Archive ``.travis.yml`` or remove it

3. **Configure Dependabot:**
   - Review and merge dependency update PRs
   - Configure auto-merge for minor/patch updates (optional)

4. **Release Process:**
   - Create a new release on GitHub
   - GitHub Actions will automatically:
     - Build distribution packages
     - Publish to PyPI
     - Build and push Docker images
     - Generate release notes

For Users
^^^^^^^^^

**No breaking changes** - The bot functionality remains the same.

**Installation:**

.. code-block:: bash

    # From PyPI (unchanged)
    pip install helga

    # From source (unchanged)
    pip install -e .

    # With development tools (new)
    pip install -e .[dev]

**Docker:**

.. code-block:: bash

    # Pull from GitHub Container Registry (new)
    docker pull ghcr.io/shaunduncan/helga:latest

    # Or build locally (unchanged)
    docker-compose up --build


Tool Comparison
---------------

Old vs New
^^^^^^^^^^

=========================== ========================== ====================================
Category                    Old                        New
=========================== ========================== ====================================
CI/CD                       Travis CI                  GitHub Actions
Linting                     flake8                     Ruff
Formatting                  Manual                     Black
Type Checking               None                       Mypy
Import Sorting              Manual                     Ruff (isort)
Security                    Manual                     Bandit + Safety
Packaging                   setup.py only              pyproject.toml
Dependencies                Manual updates             Dependabot
=========================== ========================== ====================================


Configuration Files Reference
-----------------------------

New Files
^^^^^^^^^

- ``pyproject.toml`` - Modern Python project configuration
- ``.pre-commit-config.yaml`` - Pre-commit hooks configuration
- ``.github/workflows/ci.yml`` - CI/CD pipeline
- ``.github/workflows/release.yml`` - Release automation
- ``.github/dependabot.yml`` - Dependency updates
- ``.dockerignore`` - Docker build exclusions
- ``requirements-dev.txt`` - Development dependencies

Updated Files
^^^^^^^^^^^^^

- ``Dockerfile`` - Multi-stage build, security improvements
- ``docker-compose.yml`` - Modern syntax, health checks
- ``setup.py`` - Still present for compatibility

Deprecated Files
^^^^^^^^^^^^^^^^

- ``.travis.yml`` - Replaced by GitHub Actions (can be removed)


Best Practices
--------------

Code Quality
^^^^^^^^^^^^

1. Run pre-commit hooks before committing
2. Keep code formatted with Black
3. Fix Ruff warnings
4. Add type hints to new code
5. Write tests for new features

Development Workflow
^^^^^^^^^^^^^^^^^^^^

1. Create feature branch
2. Make changes
3. Run tests locally: ``pytest``
4. Check code quality: ``pre-commit run --all-files``
5. Commit changes (pre-commit runs automatically)
6. Push and create PR
7. CI runs automatically
8. Merge after approval and passing CI

Security
^^^^^^^^

1. Review Dependabot PRs promptly
2. Check security scan results in CI
3. Keep dependencies updated
4. Use non-root user in Docker
5. Scan for vulnerabilities regularly


Troubleshooting
---------------

Pre-commit Issues
^^^^^^^^^^^^^^^^^

**Problem:** Pre-commit hooks fail

.. code-block:: bash

    # Update hooks
    pre-commit autoupdate

    # Clear cache
    pre-commit clean

    # Reinstall
    pre-commit uninstall
    pre-commit install

Docker Build Issues
^^^^^^^^^^^^^^^^^^^

**Problem:** Build fails or is slow

.. code-block:: bash

    # Clear build cache
    docker-compose build --no-cache

    # Prune unused images
    docker system prune -a

CI/CD Issues
^^^^^^^^^^^^

**Problem:** GitHub Actions fail

- Check workflow logs in GitHub Actions tab
- Verify Python version compatibility
- Check MongoDB service health
- Review dependency conflicts


Future Improvements
-------------------

Potential future enhancements:

- Add type hints to all modules
- Migrate to Python 3.10+ (drop 3.8-3.9)
- Add mutation testing
- Implement async/await patterns
- Add performance benchmarks
- Improve test coverage to 95%+
- Add integration tests
- Create plugin development guide
- Add API documentation with Swagger/OpenAPI


Resources
---------

- `PEP 621 - Project Metadata <https://peps.python.org/pep-0621/>`_
- `GitHub Actions Documentation <https://docs.github.com/en/actions>`_
- `Ruff Documentation <https://docs.astral.sh/ruff/>`_
- `Black Documentation <https://black.readthedocs.io/>`_
- `Mypy Documentation <https://mypy.readthedocs.io/>`_
- `Pre-commit Documentation <https://pre-commit.com/>`_
- `Docker Best Practices <https://docs.docker.com/develop/dev-best-practices/>`_


Questions or Issues?
--------------------

- Open an issue on GitHub: https://github.com/shaunduncan/helga/issues
- Join #helgabot on Freenode IRC
- Check documentation: https://helga.readthedocs.org

----

**Last Updated:** 2026-05-20
**Modernization Version:** 1.0
