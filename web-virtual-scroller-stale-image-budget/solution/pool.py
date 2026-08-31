# Fixed version - checks binding token, clears image on bind

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.item_id = None
        self.title = None
        self.image_url = None
        self.binding_token = 0
        self.is_bound = False

    def bind(self, item_id, title, token):
        self.item_id = item_id
        self.title = title
        self.binding_token = token
        self.is_bound = True
        self.image_url = None  # clear old image on new binding

    def unbind(self, token):
        self.item_id = None
        self.title = None
        self.image_url = None
        self.binding_token = token
        self.is_bound = False

    def apply_image(self, url, expected_token):
        if self.binding_token != expected_token:
            return False
        # Only apply if still bound (or if we want to detect corruption, unbound should not get image)
        if not self.is_bound:
            return False
        self.image_url = url
        return True

    def snapshot(self):
        if not self.is_bound:
            if self.image_url:
                return f"{self.node_id} unbound image={self.image_url}"
            return f"{self.node_id} unbound"
        img = self.image_url if self.image_url else "NONE"
        return f"{self.node_id} item={self.item_id} title={self.title} image={img}"


class VirtualPool:
    def __init__(self):
        self.nodes = {}
        self._token_counter = 0

    def _next_token(self):
        self._token_counter += 1
        return self._token_counter

    def get_node(self, node_id):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id)
        return self.nodes[node_id]

    def mount(self, node_id, item_id, title):
        token = self._next_token()
        node = self.get_node(node_id)
        node.bind(item_id, title, token)
        return token

    def unmount(self, node_id):
        token = self._next_token()
        node = self.get_node(node_id)
        node.unbind(token)
        return token

    def update_title(self, node_id, new_title):
        node = self.get_node(node_id)
        if node.is_bound:
            node.title = new_title

    def snapshot(self, node_id):
        return self.get_node(node_id).snapshot()
