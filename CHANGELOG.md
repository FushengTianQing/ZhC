# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Sphinx documentation system with API reference
- Developer guide and contributing guide
- Enhanced CI/CD pipeline with caching and parallel testing
- Issue and PR templates
- Example code improvements (hello, functions, classes)

### Changed
- Updated architecture documentation with Mermaid diagrams
- Improved code quality (score: 65 → 70)
- Reduced cyclomatic complexity (9.5 → 8.0)

## [6.0.0] - 2026-04-08

### Added
- Unified API module (`src/api/`) with `CompilationResult` and `CompilationStats`
- Configuration groups pattern (`SemanticConfig`, `OutputConfig`, `CacheConfig`, `ProfileConfig`)
- Utility modules (`src/utils/`) for file, string, and error handling
- IR intermediate representation layer
- Multiple backend support (AST and IR)

### Changed
- **BREAKING**: `compile_single_file()` and `compile_module_project()` now return `CompilationResult` instead of `bool`
- Refactored configuration system using nested dataclasses
- Optimized code complexity using Dispatch Table pattern
- Improved test coverage to 51.86%

### Fixed
- Module import issues in test suite
- Configuration initialization errors
- Various code quality issues

### Performance
- Reduced average function length (47.3 → 42.3 lines)
- Reduced high complexity functions (36 → 33)

## [5.0.0] - 2026-04-07

### Added
- Week 5 refactoring: quality improvements
- Dispatch Table pattern implementation
- State machine pattern for class parsing
- Command pattern for CLI
- Factory method pattern
- Dataclass pattern for config and errors

### Changed
- Code quality score: 65/100 (B+)
- Cyclomatic complexity: 9.5
- Test suite: 1064 passed

## [4.0.0] - 2026-03-XX

### Added
- Memory safety analysis
- Smart pointer support
- Memory syntax parsing and conversion

### Changed
- Enhanced memory management features

## [3.0.0] - 2026-03-XX

### Added
- Module system
- Import/export mechanism
- Scope management
- Dependency resolution

### Changed
- Improved module handling

## [2.0.0] - 2026-03-XX

### Added
- Class syntax parsing
- Inheritance conversion
- Virtual function support
- Operator overloading

### Changed
- Enhanced OOP features

## [1.0.0] - 2026-03-XX

### Added
- Basic project structure
- Lexer implementation
- Parser implementation
- Basic compilation pipeline

---

## Version History

| Version | Date | Description |
|:--------|:-----|:------------|
| 6.0.0 | 2026-04-08 | Unified API, IR backend, quality improvements |
| 5.0.0 | 2026-04-07 | Week 5 refactoring, design patterns |
| 4.0.0 | 2026-03-XX | Memory safety features |
| 3.0.0 | 2026-03-XX | Module system |
| 2.0.0 | 2026-03-XX | Class system |
| 1.0.0 | 2026-03-XX | Initial release |

---

**Maintainer**: ZHC Development Team
**Last Updated**: 2026-04-08