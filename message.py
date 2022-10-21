from collections.abc import MutableMapping
import utils
import json


class Message(MutableMapping):
    def __init__(self, message):
        self._store = dict(message)
        self._encoded = None

    @staticmethod
    def from_encoded(encoded):
        try:
            message = json.loads(encoded)
            if not isinstance(message, dict):
                raise utils.MessageException("JSON inválido")
            message = Message(message)
            message._encoded = encoded
            return message
        except json.JSONDecodeError:
            raise utils.MessageException("JSON inválido")

    @property
    def encoded(self):
        if self._encoded is None:
            self._encoded = json.dumps(self._store,
                                       ensure_ascii=False).encode("utf8")
        return self._encoded

    def __str__(self):
        return json.dumps(self._store, indent=4, ensure_ascii=False)

    def __repr__(self):
        return str(self._store)

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)
