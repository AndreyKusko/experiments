from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


class MockResponse:
    return_data = None
    return_status_code = None
    return_text = None
    return_content = None

    def __init__(self, data=None, status_code=None, text=None, content=None, *_a, **kwargs):
        self.return_data = data
        self.return_status_code = status_code
        self.return_text = text
        self.return_content = content
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, *_args, **_kwargs):
        return self.return_data

    def post(self, *_args, **_kwargs):
        return self.return_data

    def json(self, *_args, **_kwargs):
        if self.return_data is not None:
            return self.return_data
        return {"status": "ok"}

    @property
    def status_code(self):
        return self.return_status_code or HTTP_200_OK

    @property
    def text(self):
        return self.return_text or "Текст."

    @property
    def content(self):
        return self.return_content or "Контент"


class MockFailResponse:
    _text = "Текст ошибки."

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def json():
        data = {"status": "fail"}
        return data

    @property
    def status_code(self):
        return HTTP_400_BAD_REQUEST

    @property
    def text(self):
        return self._text

    @property
    def content(self):
        return None
