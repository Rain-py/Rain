# Notes

## System Design

### Sidecar Pattern

A sidecar service is an architectural pattern in which an additional container or process runs alongside the main application container, sharing the same lifecycle and deployment. The sidecar service provides supplementary functionality and support to the main application. It typically assists with cross-cutting concerns such as logging, monitoring, service discovery, load balancing, security, or data synchronization. The main benefit of using a sidecar service is that it can be added or removed independently of the main application, allowing modular and flexible architecture.

### Ambassador Pattern

An ambassador, also referred to as an API gateway or reverse proxy, acts as an intermediary between clients and the services within a microservices architecture. Its primary purpose is to provide a unified interface for clients to interact with multiple services. The ambassador handles requests from clients, performs tasks such as authentication, rate limiting, caching, and routing, and then forwards the requests to the appropriate microservices. It can also aggregate responses from multiple services into a single response for the client. The ambassador pattern simplifies client communication by abstracting the complexity of the underlying microservices architecture.

### Circuit Breaker

The Circuit Breaker pattern is used to handle and prevent cascading failures in distributed systems. It acts as a safety mechanism between services, monitoring requests and automatically "breaking" the circuit if a service fails or becomes unresponsive. This helps to isolate faults, prevent overloading, and provide graceful degradation. Popular implementations of this pattern include Hystrix and resilience4j.

### Saga Pattern

The Saga pattern is used to manage long-running and distributed transactions in a microservices environment. It decomposes a complex transaction into a sequence of smaller, compensating actions. Each step in the sequence represents a local transaction within a service, and if any step fails, compensating actions are executed to undo the changes made by previous steps. This pattern ensures eventual consistency across multiple services. Libraries like Eventuate and Axon provide support for implementing the Saga pattern.

### Decomposition Patterns

Decomposition patterns are used to break down a monolithic application into smaller, more manageable services. These patterns include Strangler Fig, where new functionality is gradually implemented as separate services, and the Monolithic with Modules pattern, where modules within the monolith are identified and extracted as microservices. These patterns enable the incremental migration from a monolith to a microservices architecture.

## Design Patterns

### Factory design pattern

The Factory design pattern is a creational design pattern that provides an interface for creating objects, but allows subclasses or derived classes to decide which class to instantiate. It encapsulates the object creation logic and promotes loose coupling by allowing the client code to interact with the factory interface rather than directly creating objects.

Example:

``` python
class Animal:
    def sound(self):
        pass


class Dog(Animal):
    def sound(self):
        return "Woof"


class Cat(Animal):
    def sound(self):
        return "Meow"


class AnimalFactory:
    def create_animal(self, animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        else:
            raise ValueError("Invalid animal type")


# Usage
animal_factory = AnimalFactory()
dog = animal_factory.create_animal("dog")
cat = animal_factory.create_animal("cat")

print(dog.sound())  # Output: Woof
print(cat.sound())  # Output: Meow

```

### Singleton design pattern

The Singleton design pattern is a creational design pattern that ensures that only one instance of a class is created and provides a global point of access to that instance. It is useful when you need to have a single instance of a class that provides access to shared resources, such as a database connection or a logger. The Singleton pattern is implemented by defining a static method that returns the same instance of the class every time it is called.

When creating a log service to be used by other services, the best pattern to consider is the Singleton design pattern. The Singleton pattern ensures that only one instance of the log service is created and shared among multiple components, providing a centralized and consistent logging mechanism.
