from typing import Annotated, Any

from pydantic import BeforeValidator


def normalize_email(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


EmailAddress = Annotated[str, BeforeValidator(normalize_email)]
