# Collector Architecture

The Vyn Collector consists of three major components.

## C++

Core collector.

Responsible for

- CLI
- Installation
- Removal
- Updates
- File Management
- Dependency Resolution

---

## Java

Registry backend.

Responsible for

- Metadata
- Publishing
- Validation
- Future registry server

---

## TypeScript

User Interface.

Responsible for

- Dashboard
- Package Browser
- Future GUI