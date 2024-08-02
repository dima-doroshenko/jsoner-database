def autocommit(func):

    def wrapper(*args, **kwargs):

        result = func(*args, **kwargs)

        if args[0].autocommit: args[0].commit()

        return result

    return wrapper
