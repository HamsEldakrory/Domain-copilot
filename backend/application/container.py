class Container:
    # A minimal dependency injection container.
    # Maps an abstract Port (an interface the application layer depends on) to a factory function that builds the concrete Infrastructure implementation. Deliberat

    def __init__(self):
        self._factories = {}

    def register(self, port_type, factory):
        # Register a factory function that builds a concrete implementation of the given port type.
        self._factories[port_type] = factory

    def resolve(self, port_type):
        # Return a new instance of the implementation registered for this port type.
        if port_type not in self._factories:
            raise ValueError(f"No implementation registered for {port_type}")
        return self._factories[port_type]()


container = Container()