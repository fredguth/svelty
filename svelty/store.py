# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/store.ipynb.

# %% ../nbs/store.ipynb 2
from __future__ import annotations
from typing import Callable, TypeVar,  Generic, Union, Optional, Set, Protocol

# %% auto 0
__all__ = ['T', 'covT', 'Subscriber', 'Unsubscriber', 'Updater', 'Notifier', 'StoreProtocol', 'Writable', 'Readable', 'Derived']

# %% ../nbs/store.ipynb 7
T = TypeVar("T")
covT = TypeVar("covT", covariant=True)
Subscriber = Callable[[T], None] # a callback
Unsubscriber = Callable[[], None] # a callback to be used upon termination of the subscription    
Updater = Callable[[T], T]

# %% ../nbs/store.ipynb 8
class StoreProtocol(Protocol, Generic[covT]):
    ''' The Svelte Store ~~contract~~ protocol. '''
    def subscribe(self, subscriber: Subscriber[T]) -> Unsubscriber: ...

# %% ../nbs/store.ipynb 9
class Store(StoreProtocol[T]):
    ''' A base class for all stores.'''
    value: T
    subscribers: Set[Subscriber]
    def __init__(self, /, **kwargs): 
        self.__dict__.update(kwargs) # see SimpleNamespace: https://docs.python.org/3/library/types.html
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.get()!r})"
    def subscribe(self, callback: Subscriber) -> Unsubscriber:
        return lambda: None
    def get(self) -> T: return self.value

class Readable(Store[T]): pass

class Writable(Store[T]):
    set: Subscriber
    update: Optional[Callable[[Updater],None]] = None

# %% ../nbs/store.ipynb 43
Notifier = Callable[[Subscriber], Union[Unsubscriber, None]]

# %% ../nbs/store.ipynb 44
class Writable(Store[T]):
    ''' A Writable Store.'''
    def __init__(self, 
                 initial_value: T=None, # The initial value of the store
                 start: Notifier=lambda x: None # A Notifier (Optional)
                 ) -> None:
        self.value: T = initial_value
        self.subscribers: Set[Subscriber] = set()
        self.stop: Optional[Unsubscriber] = None
        self.start: Notifier = start

    def subscribe(self, callback: Subscriber) -> Unsubscriber:
        self.subscribers.add(callback)
        if (len(self.subscribers) == 1):
            self.stop = self.start(callback) or (lambda: None)
        callback(self.value)

        def unsubscribe() -> None:
            self.subscribers.remove(callback) if callback in self.subscribers else None
            if (len(self.subscribers) == 0):
                self.stop() if self.stop else None
                self.stop = None
        return unsubscribe
    
    def set(self, new_value: T) -> None:
        if (safe_not_equal(self.value, new_value)):
            self.value = new_value
            for subscriber in self.subscribers:
                subscriber(new_value)
    
    def update(self, fn: Callable[[T], T]) -> None:
        self.set(fn(self.value))
    
    def __len__(self) -> int:
        return len(self.subscribers)

# %% ../nbs/store.ipynb 59
class Readable(Writable[T]): 
    def __init__(self, initial_value: T, start: Notifier) -> None:
        super().__init__(initial_value, start)
    def set(self, *args, **kwargs): raise Exception("Cannot set a Readable Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Readable Store.")

# %% ../nbs/store.ipynb 73
class Derived(Writable):
    ''' A Derived Store.'''
    def __init__(self,
                  source: Store, # The source store
                  fn: Updater # A function that takes the source store's value and returns a new value
                  ) -> None:
        self.target = Writable(source.get())
        self.start: Notifier = lambda x: self.target.set(fn(x))
        self.stop = source.subscribe(self.start)
    def get(self) -> T: return self.target.get()
    def set(self, *args, **kwargs): raise Exception("Cannot set a Derived Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Derived Store.")
    def subscribe(self, callback: Subscriber) -> Unsubscriber:
        return self.target.subscribe(callback)
