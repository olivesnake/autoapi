from typing import Dict, Any, List

STATUS_MAP = {
    200: "HTTP/1.1 200 OK",
    201: "HTTP/1.1 201 CREATED",
    202: "HTTP/1.1 202 ACCEPTED",
    204: "HTTP/1.1 204 NO CONTENT",
    400: "HTTP/1.1 400 BAD REQUEST",
    401: "HTTP/1.1 401 UNAUTHORIZED",
    403: "HTTP/1.1 403 FORBIDDEN",
    404: "HTTP/1.1 404 NOT FOUND",
    405: "HTTP/1.1 405 METHOD NOT ALLOWED",
    500: "HTTP/1.1 500 INTERNAL SERVER ERROR",
}


def read_as_text(filename: str) -> str:
    """
    reads a the contents of a file as a str
    :param filename: name of file
    :return: string representation of file content
    """
    with open(filename, 'r') as file:
        return file.read()


def process_headers(request_lines: List[bytes]) -> Dict:
    """
    extracts the headers from a http request
    :param request_lines: split lines of bytes from request
    :return: dictionary of keys and values
    """
    request_lines = b'\n'.join(request_lines).replace(b'\r', b'').split(b'\n')
    header_dict = {}
    for line in request_lines:
        line = line.decode()
        line = line.strip()
        res = line.split(":", maxsplit=1)
        if len(res) >= 2:
            key, val = res
            header_dict[key.strip()] = val.strip()
    return header_dict


def create_http_response(content: Any = '', headers: Dict[str, str] | None = None, code: int = 200) -> bytes:
    """
    prepares an HTTP response to send back to client
    :param content: content, if any, to send
    :param headers: optional headers for response
    :param code: response code
    :return: bytes
    """
    response = STATUS_MAP[code]
    if headers:
        response += '\r\n'.join("{}: {}".format(k, v) for k, v in headers.items())
    response += f"\r\nContent-Length: {len(content)}\r\n\r\n"
    response += content
    return response.encode("utf-8")
