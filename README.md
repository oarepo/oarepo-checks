# OARepo Checks

An extension for [invenio-checks](https://github.com/inveniosoftware/invenio-checks) that adds LLM-powered validation checks for Invenio records.

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

### 3. Configure the Check

The LLM check requires a prompt configuration. Use the provided default prompt or customize it:

```python
from oarepo_checks.config import DEFAULT_PROMPT # or any other prompt you would like to use
# current implementation assumes that there is {{record_serialized}} in prompt that would be replaced be the serialized draft/record

from invenio_checks.models import CheckConfig, Severity
from invenio_db import db

check_config_llm = CheckConfig(
        community_id=community.id, # Community ID where to add check to
        check_id="llm",  # State that we would like to use the LLM check
        severity=Severity.WARN, # Since LLM make mistakes, we would like to keep them as warnings
        enabled=True,
        params={"prompt": DEFAULT_PROMPT},
)
db.session.add(check_config_llm)
db.session.commit()


```

The prompt should instruct the LLM to return structured JSON with errors organized by sections (e.g., `metadata`, `authors`, `files`, `license`).

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
