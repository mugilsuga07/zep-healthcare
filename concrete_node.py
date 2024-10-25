from pydantic import BaseModel

class ConcreteNode(BaseModel):
    node_id: str
    content: str

    def get_content(self, metadata_mode=None):
        return self.content

    def get_metadata_str(self):
        return ""

    def get_type(self):
        return "concrete"

    def set_content(self, content):
        self.content = content

    def hash(self):
        return hash(self.node_id)


