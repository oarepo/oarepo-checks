# Using Jinja Templates for LLM Prompts

This guide explains how to use Jinja2 templates to create flexible, maintainable prompts for the LLM check system.

## Overview

The OARepo Checks library uses Jinja2 templates to generate prompts for LLM validation. This approach provides:

- Easily modify prompts without changing code
- Separate repository rules, community rules, and main prompt
- Access community metadata and other context in templates

## Template Structure

The system uses three types of templates:

1. **Repository Rules** (`repository_rules.jinja2`): Rules that apply to all records
2. **Community Rules** (`community_rules.jinja2`): Rules specific to a community
3. **Main Prompt** (`llm_prompt.jinja2`): The complete prompt structure

## Creating Custom Templates

### 1. Repository Rules Template Example

```jinja2
**General Repository Rules:**

- All titles must be descriptive
- Authors must have ORCID IDs
- Metadata must be complete

```

### 2. Community Rules Template Example

```jinja2
{% if community %}
**Community: {{ community.metadata.title }}**

{% if community.metadata.curation_policy %}
Curation Policy: {{ community.metadata.curation_policy }}
{% endif %}

Community-specific requirements apply.
{% else %}
No community-specific rules defined.
{% endif %}
```

### 3. Main Prompt Template Example

```jinja2
You are a data repository reviewer. Review the following record and identify issues.

{{ repository_rules }}

{{ community_rules }}

Record to review:
{{ record_serialized }}

Return JSON with errors grouped by section.
```

## Using the `create_prompt` Function

```python
from oarepo_checks import create_prompt
import json

# Serialize record
record_json = json.dumps(dict(record))

# Create prompt
prompt = create_prompt(
    record_serialized=record_json,
    community=community, # community record
    # Optionally override template paths:
    # prompt_template="my_custom_templates/prompt.jinja2",
    # repository_rules_template="my_custom_templates/repo_rules.jinja2",
    # community_rules_template="my_custom_templates/community_rules.jinja2",
)

# Use prompt with LLM
response = llm_client.chat_completion(prompt)
```

## Available Template Variables

### All Templates

- Any extra variables passed to `create_prompt()` via `**extra_context`

### Community Rules Template

- `community`: Community object with metadata (title, description, curation_policy, etc.)

### Main Prompt Template

- `record_serialized`: Serialized record JSON string
- `repository_rules`: Rendered repository rules
- `community_rules`: Rendered community rules

## Custom Template Variables

You can pass additional context to templates:

```python
prompt = create_prompt(
    record_serialized=record_json,
    community=community,
    # Custom variables:
    custom_rules="Additional validation rules",
    reviewer_name="Dr. Smith",
    review_date="2025-11-05",
)
```

Then use them in templates:

```jinja2
Review conducted by {{ reviewer_name }} on {{ review_date }}.
{{ custom_rules }}
```
