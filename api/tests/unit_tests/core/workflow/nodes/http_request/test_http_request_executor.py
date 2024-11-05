from core.workflow.entities.variable_pool import VariablePool
from core.workflow.nodes.http_request import (
    BodyData,
    HttpRequestNodeAuthorization,
    HttpRequestNodeBody,
    HttpRequestNodeData,
)
from core.workflow.nodes.http_request.entities import HttpRequestNodeTimeout
from core.workflow.nodes.http_request.executor import Executor


def test_executor_with_json_body_and_number_variable():
    # Prepare the variable pool
    variable_pool = VariablePool(
        system_variables={},
        user_inputs={},
    )
    variable_pool.add(["pre_node_id", "number"], 42)

    # Prepare the node data
    node_data = HttpRequestNodeData(
        title="Test JSON Body with Number Variable",
        method="post",
        url="https://api.example.com/data",
        authorization=HttpRequestNodeAuthorization(type="no-auth"),
        headers="Content-Type: application/json",
        params="",
        body=HttpRequestNodeBody(
            type="json",
            data=[
                BodyData(
                    key="",
                    type="text",
                    value='{"number": {{#pre_node_id.number#}}}',
                )
            ],
        ),
    )

    # Initialize the Executor
    executor = Executor(
        node_data=node_data,
        timeout=HttpRequestNodeTimeout(connect=10, read=30, write=30),
        variable_pool=variable_pool,
    )

    # Check the executor's data
    assert executor.method == "post"
    assert executor.url == "https://api.example.com/data"
    assert executor.headers == {"Content-Type": "application/json"}
    assert executor.params == {}
    assert executor.json == {"number": 42}
    assert executor.data is None
    assert executor.files is None
    assert executor.content is None

    # Check the raw request (to_log method)
    raw_request = executor.to_log()
    assert "POST /data HTTP/1.1" in raw_request
    assert "Host: api.example.com" in raw_request
    assert "Content-Type: application/json" in raw_request
    assert '{"number": 42}' in raw_request


def test_executor_with_json_body_and_object_variable():
    # Prepare the variable pool
    variable_pool = VariablePool(
        system_variables={},
        user_inputs={},
    )
    variable_pool.add(["pre_node_id", "object"], {"name": "John Doe", "age": 30, "email": "john@example.com"})

    # Prepare the node data
    node_data = HttpRequestNodeData(
        title="Test JSON Body with Object Variable",
        method="post",
        url="https://api.example.com/data",
        authorization=HttpRequestNodeAuthorization(type="no-auth"),
        headers="Content-Type: application/json",
        params="",
        body=HttpRequestNodeBody(
            type="json",
            data=[
                BodyData(
                    key="",
                    type="text",
                    value="{{#pre_node_id.object#}}",
                )
            ],
        ),
    )

    # Initialize the Executor
    executor = Executor(
        node_data=node_data,
        timeout=HttpRequestNodeTimeout(connect=10, read=30, write=30),
        variable_pool=variable_pool,
    )

    # Check the executor's data
    assert executor.method == "post"
    assert executor.url == "https://api.example.com/data"
    assert executor.headers == {"Content-Type": "application/json"}
    assert executor.params == {}
    assert executor.json == {"name": "John Doe", "age": 30, "email": "john@example.com"}
    assert executor.data is None
    assert executor.files is None
    assert executor.content is None

    # Check the raw request (to_log method)
    raw_request = executor.to_log()
    assert "POST /data HTTP/1.1" in raw_request
    assert "Host: api.example.com" in raw_request
    assert "Content-Type: application/json" in raw_request
    assert '"name": "John Doe"' in raw_request
    assert '"age": 30' in raw_request
    assert '"email": "john@example.com"' in raw_request


def test_executor_with_json_body_and_nested_object_variable():
    # Prepare the variable pool
    variable_pool = VariablePool(
        system_variables={},
        user_inputs={},
    )
    variable_pool.add(["pre_node_id", "object"], {"name": "John Doe", "age": 30, "email": "john@example.com"})

    # Prepare the node data
    node_data = HttpRequestNodeData(
        title="Test JSON Body with Nested Object Variable",
        method="post",
        url="https://api.example.com/data",
        authorization=HttpRequestNodeAuthorization(type="no-auth"),
        headers="Content-Type: application/json",
        params="",
        body=HttpRequestNodeBody(
            type="json",
            data=[
                BodyData(
                    key="",
                    type="text",
                    value='{"object": {{#pre_node_id.object#}}}',
                )
            ],
        ),
    )

    # Initialize the Executor
    executor = Executor(
        node_data=node_data,
        timeout=HttpRequestNodeTimeout(connect=10, read=30, write=30),
        variable_pool=variable_pool,
    )

    # Check the executor's data
    assert executor.method == "post"
    assert executor.url == "https://api.example.com/data"
    assert executor.headers == {"Content-Type": "application/json"}
    assert executor.params == {}
    assert executor.json == {"object": {"name": "John Doe", "age": 30, "email": "john@example.com"}}
    assert executor.data is None
    assert executor.files is None
    assert executor.content is None

    # Check the raw request (to_log method)
    raw_request = executor.to_log()
    assert "POST /data HTTP/1.1" in raw_request
    assert "Host: api.example.com" in raw_request
    assert "Content-Type: application/json" in raw_request
    assert '"object": {' in raw_request
    assert '"name": "John Doe"' in raw_request
    assert '"age": 30' in raw_request
    assert '"email": "john@example.com"' in raw_request


def test_extract_selectors_from_template_with_newline():
    variable_pool = VariablePool()
    variable_pool.add(("node_id", "custom_query"), "line1\nline2")
    node_data = HttpRequestNodeData(
        title="Test JSON Body with Nested Object Variable",
        method="post",
        url="https://api.example.com/data",
        authorization=HttpRequestNodeAuthorization(type="no-auth"),
        headers="Content-Type: application/json",
        params="test: {{#node_id.custom_query#}}",
        body=HttpRequestNodeBody(
            type="none",
            data=[],
        ),
    )

    executor = Executor(
        node_data=node_data,
        timeout=HttpRequestNodeTimeout(connect=10, read=30, write=30),
        variable_pool=variable_pool,
    )

    assert executor.params == {"test": "line1\nline2"}
