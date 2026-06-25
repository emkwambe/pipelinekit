# PipelineKit Naming Conventions

## Files

Use descriptive kebab-case or stable numbered prefixes.

Examples:

SPEC-001-CLI-Framework.md

ADR-003-Adopt-dlt.md

## CLI Commands

Use lowercase verbs.

Examples:

pipelinekit init

pipelinekit validate

pipelinekit run

pipelinekit doctor

## Python Packages

Use snake_case.

Examples:

pipelinekit.core

pipelinekit.adapters

pipelinekit.contracts

## Classes

Use PascalCase.

Examples:

PipelineRunner

ContractValidator

LLMProvider

## Functions

Use snake_case.

Examples:

load_config

validate_contract

run_pipeline

## Errors

Use PascalCase ending in Error.

Examples:

PipelineKitError

ConfigurationError

ContractViolationError
