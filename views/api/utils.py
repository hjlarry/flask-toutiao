import functools

from flask import json
from werkzeug.wrappers import Response

from corelib.flask_ import Flask


class ApiResult:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status

    def to_response(self):
        if "r" not in self.data:
            self.data["r"] = 0
        return Response(
            json.dumps(self.data), mimetype="application/json", status=self.status
        )


class ApiFlask(Flask):
    def make_response(self, receive):
        if isinstance(receive, Response):
            return receive

        if isinstance(receive, (dict, list)):
            data = {"data": receive}
            receive = ApiResult(data)
        if isinstance(receive, ApiResult):
            return receive.to_response()

        return Flask.make_response(self, receive)
