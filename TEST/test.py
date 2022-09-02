

def checkNull(func):
    def wrapper(*args, **kwargs):
        if not all( [False for val in kwargs.values() if val is None]): return None
        if not all( [False for arg in args if arg is None]): return None
        return func(*args, **kwargs)
    return wrapper

def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate

@for_all_methods(checkNull)
class Converters():

    @staticmethod
    def myfunc(x):
        return x


x = Converters.myfunc(2)
print(x)