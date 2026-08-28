# OARepo Checks

An extension for [invenio-checks](https://github.com/inveniosoftware/invenio-checks) that adds LLM-powered validation checks for Invenio records.

## Features

This library provides:

- **LLM-powered validation checks** - Validate records using configurable Large Language Models
- **Jinja2 templates** - Define prompts using Jinja2 templates (see [TEMPLATES.md](TEMPLATES.md))
- **Service components** - Two components for integrating checks into your Invenio application:
  - `OARepoChecksComponents` - Triggers checks on record creation
  - `RegisterCheckComponent` - Automatically creates and updates check configurations when communities are created or modified
- **CLI tool** - Command-line interface for managing LLM checks across communities

## Configuration

### 1. Define LLM Client

  Configure the LLM client through `oarepo-config`:

```python
  from oarepo_config import config

  config.configure_llm(
      api_token="token",
  )
```
  Available parameters:

  - api_token (required) - API token used by the LLM provider. Commonly loaded from INVENIO_OAREPO_CHECKS_TOKEN.
  - enabled (default: True) - Enables or disables LLM checks configuration.
  - client_name (default: "chat_einfra") - Name under which the client is registered.
  - api_url (default:  "https://llm.ai.e-infra.cz/v1/chat/completions") - Chat completion endpoint URL.
  - model (default:  "nrp") - Model used for completions.
  - fallback_community (default: None) - Community slug used when a record has no community.
  - as_default (default: True) - Sets the registered client as the default OARepo Checks LLM client.

LLM checks are configured per community. If a record is not submitted to a real community, OARepo Checks can use a configured fallback community instead.


### 3. When LLM Checks Run

LLM checks are executed asynchronously. When a draft is submitted to a community, the check configuration for that community is used and the LLM validation runs in the background.

For records submitted through the publish workflow without a community, the LLM check is triggered when the submit-to-publish request is created. In this case, the configured fallback community is used.

### 4. Creating Custom LLM Clients

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
OAREPO_CHECKS_LLM_CLIENTS = {"custom": CustomLLMClient(api_key="your-key", endpoint="https://your-llm-api.com/chat")}
```

### 5. Manually Configure the Check

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
        "prompt": "Some very good prompt to check for mistakes",
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

# Create prompt from templates
prompt = create_prompt(
    record_serialized=json.dumps(dict(record)),
    community=community,  # Community record (optional)
    # Optionally override default templates:
    # prompt_template="custom_templates/my_prompt.jinja2",
)
```

The prompt should instruct the LLM to return structured JSON with errors organized by sections (e.g., `metadata`, `authors`, `files`, `license`).

This component will trigger validation checks immediately when a new record/draft is created.

## Service Components

This library provides two service components to integrate checks into your Invenio application:

### 1. OARepoCheckComponents

This component triggers LLM checks when records are created and is built on top of Invenio ChecksComponent. Furthermore
it returns generic community ID on record without communities
which enables to run checks on records/drafts without predefined community.

You need to replace Invenio `ChecksComponents` with `OARepoChecksComponent` in `RDM_RECORDS_SERVICE_COMPONENTS`

### 2. RegisterCheckComponent

This component automatically creates and updates LLM check configurations when communities are created or modified. It generates community-specific prompts using Jinja2 templates. By default all LLM checks are **enabled**. You can disable/enable them by using CLI commands (see below). Add it to your communities service:

```python
from invenio_communities.services.components import DefaultCommunityComponents
from oarepo_checks.services.components.register_check_config import RegisterCheckComponent

# In your invenio.cfg or app configuration
app_config["COMMUNITIES_SERVICE_COMPONENTS"] = [*DefaultCommunityComponents, RegisterCheckComponent]
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
  }
}
```
