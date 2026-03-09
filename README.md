# Clustered Index - B+ Tree File Organization

Educational project implementing a **clustered indexed file** using a
**B+ Tree** structure.\
The system simulates disk-based storage with page-level I/O and provides
tools for experimentation, visualization, and performance analysis.

The goal of this project was to explore how database storage engines
manage indexed files and disk access patterns.

This repository contains:

-   Implementation of a **B+ Tree based clustered index**
-   A **page manager** simulating disk I/O
-   Binary file storage for pages and records
-   A **TUI interface** for interacting with the tree
-   **Experiments for measuring I/O performance**
-   **Visualization of the tree structure**
-   Automated tests
-   A detailed **project report (PL + EN)**

------------------------------------------------------------------------

# Architecture Overview

The system simulates how a database engine stores indexed records on
disk.

    User / TUI
         |
         v
    +-------------------+
    | B+ Tree           |
    |-------------------|
    | insert            |
    | delete            |
    | search            |
    +-------------------+
         |
         v
    +-------------------+
    | Page Manager      |
    |-------------------|
    | read_page()       |
    | write_page()      |
    | IO statistics     |
    +-------------------+
         |
         v
    +-------------------+
    | Binary File       |
    |-------------------|
    | FileHeader        |
    | PageHeader        |
    | Records           |
    +-------------------+

The system mimics disk operations by reading and writing **fixed-size
pages**.

------------------------------------------------------------------------

# Key Concepts Implemented

## Clustered Index

A **clustered index** stores records in the same physical order as the
index key.

In this implementation:

-   records are stored directly in the leaf nodes
-   leaf nodes form a linked list
-   internal nodes store key separators

------------------------------------------------------------------------

## B+ Tree

The project implements a full **B+ Tree** including:

-   insertion
-   node splitting
-   search
-   leaf chaining
-   internal node management

The tree is configurable through the **Config** class.

    core/config.py

Configuration allows control over:

-   page size
-   maximum records per page
-   tree order
-   experiment parameters

------------------------------------------------------------------------

# Storage Layer

The system simulates disk storage using binary files.

## File Header

Stores metadata about the indexed file.

Example fields:

- page size
- root page pointer
- number of pages



```
core/structures/file_header.py
```

## Page Structure

Each page contains:

-   page header
-   records
-   pointers (for internal nodes)


------------------------------------------------------------------------

## Records

Data entries stored in leaf pages.
```
core/structures/record.py
```

------------------------------------------------------------------------

# Page Manager

The **Page Manager** simulates disk I/O operations.

Responsibilities:

-   reading pages from disk
-   writing pages to disk
-   counting I/O operations
-   simulating page cache behaviour

```
core/page_manager.py
```
This allows performance experiments similar to real database systems.

------------------------------------------------------------------------

# Experiments

The project contains an **experiment framework** for measuring B+ Tree
performance.
```
 experiment/
```
Experiments collect metrics such as:

-   number of disk reads
-   number of disk writes
-   tree height
-   operation performance

Results can be exported and analyzed later.

------------------------------------------------------------------------

# Visualization and TUI

The project includes a **Terminal User Interface** for interacting with
the system. 
```
tui.py
```

Capabilities:

-   visualize the B+ tree structure
-   insert records
-   delete records
-   clear indexed file
-   run custom experiments
-   inspect page structure

The visualization helps understand how the tree evolves during
operations.

------------------------------------------------------------------------

# Project Structure

    clustered-index
    │
    ├── core
    │   ├── bplus_tree.py
    │   ├── config.py
    │   ├── page_manager.py
    │   │
    │   └── structures
    │       ├── file_header.py
    │       ├── page.py
    │       └── record.py
    │
    ├── experiment
    │   ├── experiment_data.py
    │   ├── metrics.py
    │   └── tree_experiment_runner.py
    │
    ├── tests
    │   ├── test_bplus_tree.py
    │   ├── test_page_manager.py
    │   ├── test_page.py
    │   ├── test_experiment.py
    │   └── test_system.py
    │
    ├── docs
    │   ├── report_en.pdf
    │   └── report_pl.pdf
    │
    ├── data
    │
    ├── tui.py
    ├── main.py
    └── requirements.txt

------------------------------------------------------------------------

# Running the Project

## Install dependencies
```
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Run the application
```
python main.py
```
------------------------------------------------------------------------

# Running Experiments

Experiments can be run through the experiment runner.
```
experiment/tree_experiment_runner.py
```
They generate data about I/O operations and tree behavior.

Example metrics:

-   number of page reads
-   number of page writes
-   tree height
-   insert performance

------------------------------------------------------------------------

# Running Tests

The project includes a comprehensive test suite.

Run tests using:
```
pytest
```
Test categories include:

-   B+ Tree logic
-   Page structure
-   Page manager
-   experiments
-   system-level behavior

------------------------------------------------------------------------

# Documentation

A detailed report describing the implementation and experiments is
included:
```
docs/report_en.pdf
docs/report_pl.pdf
```
The report explains:

-   theoretical background
-   B+ Tree algorithms
-   storage layout
-   experiment methodology
-   performance results

------------------------------------------------------------------------
