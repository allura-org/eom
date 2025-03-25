from msgspec import Struct

class Child(Struct):
    test: str

class ChildProxy:
    def __init__(self, child: Child, parent):
        self._child = child
        self._parent = parent
        
    def __getattr__(self, name):
        return getattr(self._child, name)
        
    def __setattr__(self, name, value):
        if name in ('_child', '_parent'):
            object.__setattr__(self, name, value)
        else:
            print(f"Intercepted modification: {name} = {value}")
            self._parent._on_child_modified(name, value)
            setattr(self._child, name, value)

class Parent(Struct):
    _child: Child

    @property
    def child(self) -> Child:
        print("child getter called")
        # Return a proxy instead of the actual child
        return ChildProxy(self._child, self)

    @child.setter
    def child(self, value: Child):
        print("child setter called")
        self._child = value
        
    def _on_child_modified(self, attr_name, new_value):
        print(f"Parent notified: child.{attr_name} changed to {new_value}")

parent = Parent(_child=Child(test="test"))

print(parent.child.test)
parent.child.test = "test2"  # This will now be intercepted
print(parent.child.test)

