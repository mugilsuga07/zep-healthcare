class Document:
    def __init__(self, text, metadata):
        self.text = text
        self.metadata = metadata

    def get_embedding(self):
        return [0.0] * 1536

    def get_content(self, metadata_mode=None):
        return self.text

    def get_metadata(self):
        return self.metadata

    def node_id(self):
        from uuid import uuid4
        return str(uuid4())

    def set_content(self, content):
        self.text = content







