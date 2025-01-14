import dataclasses
import json
import logging
from typing import AsyncGenerator
from error import error_dict

class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling dataclasses.
    
    This encoder extends the default `json.JSONEncoder` to support Python dataclasses.
    When an object is an instance of a dataclass, it is serialized as a dictionary
    using `dataclasses.asdict`. If not a dataclass, the default serialization behavior
    is used.
    
    Args:
        o: The object to serialize.
    
    Returns:
        Serialized dictionary if the object is a dataclass, otherwise the default 
        serialization for other types.
    """
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)

async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """
    Formats an asynchronous generator of dictionaries into newline-delimited JSON (NDJSON).
    
    This function processes an asynchronous generator of dictionary objects, serializing 
    each item as a JSON string with custom handling for dataclasses. The result is returned 
    as a newline-delimited JSON (NDJSON) format, where each JSON object is followed by a 
    newline character. In case of any errors during processing, they are caught, logged, 
    and returned in the stream as a JSON error response.

    Args:
        r: An asynchronous generator yielding dictionary objects.
    
    Yields:
        An asynchronous generator of NDJSON-formatted strings.
        
    Raises:
        Exception: Any exception during processing is logged and an error response is returned.
    """
    try:
        async for event in r:
            yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps(error_dict(error))