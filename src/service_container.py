class ServiceContainer:
    """
    A simple dependency injection container that manages service instances.
    """
    def __init__(self):
        self._services = {}
    
    def register(self, service_name, instance):
        """Register a service instance with a name"""
        self._services[service_name] = instance
        return self
    
    def get(self, service_name):
        """Get a registered service by name"""
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not registered")
        return self._services[service_name]
    
    def has(self, service_name):
        """Check if a service is registered"""
        return service_name in self._services
