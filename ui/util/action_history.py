class ActionHistory:
    def __init__(self):
        self.id = 0           # Counter for the current ID of objects
        self.undo_stack = {}  # Stack to keep track of undo actions
        self.redo_stack = {}  # Stack to keep track of redo actions

    def add_action(self, object_on_stack):
        """
        Add a new action to the history. This clears the redo stack.
        """
        self.undo_stack[self.id] = object_on_stack

    def undo(self):
        """
        Undo the last action.
        Returns the row_id and actors for the undone action.
        """
        if not self.undo_stack:
            return None
        last_id = max(self.undo_stack.keys())
        object_on_stack = self.undo_stack.pop(last_id)
        self.redo_stack[last_id] = object_on_stack
        return object_on_stack

    def redo(self):
        """
        Redo the last undone action.
        Returns the row_id and actors for the redone action.
        """
        if not self.redo_stack:
            return None
        last_id = max(self.redo_stack.keys())
        object_on_stack = self.redo_stack.pop(last_id)
        self.undo_stack[last_id] = object_on_stack
        return object_on_stack

    def remove_by_id(self, id: int):
        """
        Remove action by ID from both undo and redo stacks.
        """
        if id in self.undo_stack:
            del self.undo_stack[id]
        if id in self.redo_stack:
            del self.redo_stack[id]

    def get_id(self):
        return self.id

    def decrementIndex(self):
        self.id -= 1

    def incrementIndex(self):
        self.id += 1

    def clearIndex(self):
        self.id = 0
