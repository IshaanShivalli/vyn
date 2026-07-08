# Vyn Collector

The official dependency collector for the **Vyn Programming Language**.

Vyn Collector manages external **libraries** and **packages** for Vyn. It downloads them from the official `vyn-lib` repository and installs them into the user's dependency directory.

The collector is written primarily in **C++**, with supporting modules in **Java** and **TypeScript**.

---

# Features

- Install libraries
- Install packages
- Remove libraries
- Remove packages
- Update libraries
- Update packages
- Update everything
- Search packages
- Search libraries
- View installed package information
- View installed library information
- GitHub registry support
- Dependency management
- Local package cache
- Logging

---

# Repository Structure

```
collector/
│
├── include/
├── src/
├── cpp/
├── java/
├── typescript/
│
├── registry/
├── cache/
├── logs/
│
├── CMakeLists.txt
├── README.md
└── LICENSE
```

---

# Commands

## Install Library

```bash
vyn -lib install <library>
```

Example

```bash
vyn -lib install graphics
```

---

## Install Package

```bash
vyn -pack install <package>
```

Example

```bash
vyn -pack install discord
```

---

## Delete Library

```bash
vyn -del -lib <library>
```

Example

```bash
vyn -del -lib graphics
```

---

## Delete Package

```bash
vyn -del -pack <package>
```

Example

```bash
vyn -del -pack discord
```

---

## Update All

```bash
vyn -U -A
```

---

## Update Libraries

```bash
vyn -U -lib
```

---

## Update Packages

```bash
vyn -U -pack
```

---

## Show Library

```bash
vyn -show -lib <library>
```

Example

```bash
vyn -show -lib graphics
```

Output

```
Library : graphics
Version : 1.2.0
Author  : Ishaan
Status  : Latest
```

---

## Show Package

```bash
vyn -show -pack <package>
```

Example

```bash
vyn -show -pack discord
```

---

## Search Libraries

```bash
vyn -search -lib <name>
```

---

## Search Packages

```bash
vyn -search -pack <name>
```

---

# How It Works

The collector checks the official Vyn registry.

```
vyn-lib
│
├── libraries/
├── packages/
└── registry/
```

The required files are downloaded from GitHub and installed into

```
vyn-dependencies/
│
├── libraries/
└── packages/
```

Built-in libraries remain inside the Vyn interpreter and are **not** managed by the collector.

---

# Supported File Types

The collector can install any supported source file including

```
.vyn
.py
.cpp
.hpp
.c
.h
.js
.ts
.java
.json
.toml
.yaml
.yml
.xml
.txt
.md
```

---

# Technologies

- C++
- Java
- TypeScript
- CMake

---

# Roadmap

- GitHub integration
- Dependency resolution
- Version checking
- Automatic updates
- Package publishing
- Multiple registries
- Registry mirrors
- Authentication
- Digital signatures
- GUI package manager

---

# License

This project is licensed under the MIT License.

---

# Author

**Ishaan Shivalli**

Creator of the **Vyn Programming Language** and the **Vyn Collector**.