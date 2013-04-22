class Visitable(object):

    def _friend_accept_visitor(self, visitor):
        raise NotImplementedError("Visitable is an abstract class")


class Observable(object):

    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, notification):
        for observer in self._observers:
            observer.on_notify_observers(notification)


class Observer(object):

    def on_notify_observers(self, notification):
        raise NotImplementedError("Observer is an abstract class")


class ObserverNotification(object):
    pass
