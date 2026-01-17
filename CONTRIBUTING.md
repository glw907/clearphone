# Contributing to Clearphone

Thank you for your interest in contributing to Clearphone! This project is in early development, and contributions are welcome once the core is stable.

## Project Status

**Current version:** 0.1.0 (CLI prototype)
**Status:** Active development

We're currently building the core functionality. Once the CLI prototype is complete and tested, we'll welcome contributions more broadly.

## How to Contribute

### Device Profiles

The most valuable contributions are **device profiles** from users who own and test on specific devices.

To become a device maintainer:

1. **Test the tool** on your device thoroughly
2. **Create or update a device profile** in `device-profiles/`
3. **Commit to maintenance** — keep it current with OS updates
4. **Test changes** on real hardware before submitting

Device profiles should follow the schema in `docs/profile-schema.md`.

### Bug Reports

If you encounter issues:

1. Check existing issues to avoid duplicates
2. Include:
   - Device model and Android version
   - Profile being used
   - Complete error message
   - Steps to reproduce
3. Tag appropriately (bug, device-specific, etc.)

### Feature Requests

For new features:

1. Check if it aligns with project goals (minimal, focused, low-distraction)
2. Explain the use case clearly
3. Consider implementation complexity
4. Open an issue for discussion before coding

## Development Setup

```bash
# Clone the repository
git clone https://github.com/glw907/clearphone.git
cd clearphone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format and lint
ruff check --fix .
ruff format .
```

## Code Standards

Read `CLAUDE.md` for detailed development guidelines. Key points:

### Python Style

- **Python 3.11+** required
- **Type hints** on all functions
- **Google-style docstrings**
- **Absolute imports only** (no relative imports)
- **Format with ruff** before committing

### Testing

- All new features require tests
- Mock external dependencies (ADB, HTTP requests)
- Test edge cases explicitly (Knox-protected packages, network timeouts, etc.)
- Aim for high coverage of core logic

### Error Handling

- **Fail fast** on validation errors
- **Continue with warnings** on recoverable errors (package can't be removed)
- **Abort immediately** on critical errors (device disconnected)
- Error messages must explain what happened AND how to fix it

### Documentation

- Update `CLAUDE.md` for implementation details
- Update `README.md` for user-facing changes
- Follow terminology in `docs/style-guide.md`
- Keep both files in sync for architecture changes

## Commit Guidelines

- **Clear, descriptive commit messages**
- Reference issues when applicable (`Fixes #123`)
- One logical change per commit
- Test before committing

### Commit Message Format

```
Brief summary (50 chars or less)

More detailed explanation if needed. Explain what and why,
not how (the code shows how).

Fixes #123
```

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Write tests** for your changes
3. **Run the test suite** and ensure all tests pass
4. **Format code** with ruff
5. **Update documentation** (README.md, CLAUDE.md, docs/)
6. **Submit a pull request** with a clear description

### PR Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Made in this PR

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted with ruff
- [ ] Documentation updated
- [ ] No breaking changes (or documented if unavoidable)
```

## What We're NOT Accepting (v0.1.0)

To keep the project focused during early development:

- GUI implementations (CLI/TUI only for now)
- Play Store integration (F-Droid + direct APK only)
- Root-required operations (rootless ADB only)
- Custom ROM support (stock Android focus)
- Device profiles without real hardware testing

## Code of Conduct

Be respectful, constructive, and collaborative. This project is about giving users control over their devices — let's model that in how we work together.

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0 (GPL-3.0), the same license as the project.

All new Python files must include the GPL v3 license header (see `CLAUDE.md` for the template).

## Questions?

Open an issue or start a discussion. We're happy to help!

---

Thank you for contributing to Clearphone!
