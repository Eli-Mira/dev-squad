# dev-squad

A multi-agent development team simulation for code quality, security, and architecture review.

## Overview

`dev-squad` runs a coordinated team of specialized agents to review your codebase:
- **Architect** - architecture boundaries, module structure
- **Security** - OWASP Top 10, secrets, auth patterns
- **Quality** - code style, maintainability, test coverage
- **Performance** - bottlenecks, profiling, optimization

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run the squad on a codebase
python -m dev_squad --path /path/to/your/project
```

## Requirements

- Python 3.11+
- Git repository to analyze

## Architecture

```
dev-squad/
├── scripts/
│   └── dev_squad.py          # CLI entry point
└── src/
    └── dev_squad_pipeline.py # Multi-agent orchestration
```

## License

MIT License — see [LICENSE](LICENSE)
