# OARepo Checks

An extension for [invenio-checks](https://github.com/inveniosoftware/invenio-checks) that adds LLM-powered validation checks for Invenio records.

## Features

This library provides:

- **LLM-powered validation checks** - Validate records using configurable Large Language Models
- **Jinja2 templates** - Define prompts using Jinja2 templates
- **Service components** - Two components for integrating checks into your Invenio application:
  - `OARepoChecksComponents` - Triggers checks on record creation
  - `RegisterCheckComponent` - Automatically creates and updates check configurations when communities are created or modified
- **CLI tool** - Command-line interface for managing LLM checks across communities

## Configuration

### 1. Define LLM Clients

Configure one or more LLM clients in your Invenio application configuration:

```python
from oarepo_checks.llm_client import ChatEInfraClient

# In your invenio.cfg or app configuration
OAREPO_CHECKS_LLM_CLIENTS = {
    "chat_einfra": ChatEInfraClient(
        api_token="your-api-token",
        api_url="https://chat.ai.e-infra.cz/api/chat/completions",  # optional, this is default
        model="deepseek-r1"  # optional, this is default
    )
}

# Set the default client to use
OAREPO_CHECKS_DEFAULT_LLM_CLIENT = "chat_einfra"
```

### 2. Creating Custom LLM Clients

You can create custom clients by inheriting from `BaseLLMClient`:

```python
from oarepo_checks.llm_client import BaseLLMClient
import requests

class CustomLLMClient(BaseLLMClient):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    def chat_completion(self, prompt: str, **kwargs) -> str:
        """
        Send a prompt to your LLM API and return JSON response.

        Returns:
            str: A valid JSON string with validation results
        """
        # Your implementation here
        ...

# Register in configuration
OAREPO_CHECKS_LLM_CLIENTS = {
    "custom": CustomLLMClient(
        api_key="your-key",
        endpoint="https://your-llm-api.com/chat"
    )
}
```

### 3. Manually Configure the Check

The LLM check uses Jinja2 templates for flexible prompt configuration. You can either use the default templates or create custom ones.

#### Using Default Templates

```python
from invenio_checks.models import CheckConfig, Severity
from invenio_db import db

check_config_llm = CheckConfig(
    community_id=community.id,  # Community ID where to add check to
    check_id="llm",  # State that we would like to use the LLM check
    severity=Severity.WARN,  # Since LLM make mistakes, we would like to keep them as warnings
    enabled=True,
    params={
        "prompt_template": "oarepo_checks/llm_prompt.jinja2",
        "repository_rules_template": "oarepo_checks/repository_rules.jinja2",
        "community_rules_template": "oarepo_checks/community_rules.jinja2",
    },
)
db.session.add(check_config_llm)
db.session.commit()
```

#### Using the Prompt Creation Utility

You can also create prompts programmatically:

```python
from oarepo_checks import create_prompt
import json

# Get community (optional)
community = current_communities.service.record_cls.pid.resolve(community_id)

# Create prompt from templates
prompt = create_prompt(
    record_serialized=json.dumps(dict(record)),
    community=community,
    # Optionally override default templates:
    # prompt_template="custom_templates/my_prompt.jinja2",
)
```

The prompt should instruct the LLM to return structured JSON with errors organized by sections (e.g., `metadata`, `authors`, `files`, `license`).

### 4. Enable Checks on Record Creation (Optional)

By default, invenio-checks runs on record updates or by using a review section under parent information. If you want to also run checks when records are first created, add the `ChecksOnCreateComponent` to your service components:

```python
from invenio_rdm_records.services.components import DefaultRecordsComponents
from oarepo_checks.services.components.checks import ChecksOnCreateComponent

# In your invenio.cfg or app configuration
app_config["RDM_RECORDS_SERVICE_COMPONENTS"] = [
    *DefaultRecordsComponents,
    ChecksOnCreateComponent
]
```

This component will trigger validation checks immediately when a new record/draft is created.

## Service Components

This library provides two service components to integrate checks into your Invenio application:

### 1. OARepoChecksComponents

This component triggers LLM checks when records are created and is built on top of Invenio ChecksComponent. Furthermore
it returns generic community ID on record without communities
which enables to run checks on records/drafts without predefined community.

You need to replace Invenio ChecksComponents with OARepoChecksComponent
in `RDM_RECORDS_SERVICE_COMPONENTS`

### 2. RegisterCheckComponent

This component automatically creates and updates LLM check configurations when communities are created or modified. It generates community-specific prompts using Jinja2 templates. Add it to your communities service:

```python
from invenio_communities.services.components import DefaultCommunityComponents
from oarepo_checks.services.components.register_check_config import RegisterCheckComponent

# In your invenio.cfg or app configuration
app_config["COMMUNITIES_SERVICE_COMPONENTS"] = [
    *DefaultCommunityComponents,
    RegisterCheckComponent
]
```

When a community is created, this component:

- Automatically creates a `CheckConfig` for the LLM check
- Generates a prompt with community-specific rules using templates
- Sets the check severity to `WARN` by default

When a community is updated, it regenerates the prompt to reflect any changes to community metadata.

## CLI Commands

The library includes a CLI tool for managing LLM checks across communities:

### Enable/Disable LLM checks

```bash
# Disable LLM check for a specific community
oarepo checks disable-llm-check <community-slug>

# Enable LLM check for a specific community
oarepo checks enable-llm-check <community-slug>
```

### Update prompts

```bash
# Update prompts for all communities (regenerates with latest templates)
oarepo checks update-prompts

# Update prompt for a specific community only
oarepo checks update-prompts --community-slug <community-slug>
```

This is useful when:

- You've updated your Jinja2 templates and want to apply changes to existing communities
- Community metadata has been modified outside the normal update workflow
- You need to batch-regenerate prompts after configuration changes

## Usage

Once configured, the LLM check integrates with invenio-checks. It will:

1. Serialize the record to JSON
2. Send it to the configured LLM with your prompt
3. Parse the LLM response for validation errors
4. Return structured error messages organized by field/section

The check runs automatically when records are created or updated, based on your invenio-checks configuration.

## Expected LLM Response Format

The LLM should return JSON in similar structure:

```json
{
  "metadata.title": {                                                   # path for that specific field
    "section_empty": false,                                             # LLM found some errors
    "errors": [
      {
        "error_short": "Brief error description",                       # provide a short and long description
        "error_long": "Detailed explanation and suggestions for fix",
        "manual_check_needed": false                                    # additional flag that can be used later
      }
    ]
  },
  "metadata.license": {
    "section_empty": true,                                              # if no errors are found by the LLM, then it set section_empty = True to know that LLM still checked this section
    "errors": []
  }
}
```

## Requirements

- Python >= 3.13
- invenio-checks >= 2.0.0
- oarepo >= 14.0.0

## License

MIT License - see LICENSE file for details.
