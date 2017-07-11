from collections import namedtuple
import queue
from contextlib import contextmanager

ResourceQueuePair = namedtuple("ResourceQueuePair",["ret","req"])

class ResourceNotAvailable(Exception):
    pass

class ReturnTimeout(Exception):
    pass


class Resource(object):
    '''
    An object that contains a resource that is only 
    allowed to be accessed by one thread at one time

    Like a thread lock, but safer because the resource
    is only ever exposed from inside a context manager,
    which means it is always released.
    '''

    def __init__(self,*,c_func, c_args=(), c_kwargs={} ):
        self.c_func = c_func
        self.c_args = c_args
        self.c_kwargs = c_kwargs
        self.q_req = queue.Queue(maxsize=1)
        self.q_ret = queue.Queue(maxsize=1)

    def _construct(self):
        return self.c_func(*self.c_args, **self.c_kwargs)

    def request(self,timeout):
        try:
            return self.q_req.get(timeout=timeout)
        except queue.Empty:
            raise ResourceNotAvailable

    def return_(self):
        self.q_ret.put(False)

    def close(self):
        self.q_ret.put(True)

    def _make_available(self,resource):
        self.q_req.put(resource)

    def _is_returned(self,*,timeout):
        try:
            return self.q_ret.get(timeout=timeout)
        except queue.Empty:
            raise ReturnTimeout

    def box(self):
        '''
        Coordinates access to the resource.

        Must run in its own thread.

        '''
        resource = self._construct()

        self._make_available(resource)
        while True:
            try:
                close_box = self._is_returned(timeout=0.1)
                if close_box:
                    break
                self._make_available(resource)
            except ReturnTimeout:
                pass

    @contextmanager
    def access(self,timeout=1):
        """
        Context Manager for accessing a resource
        example:
        with resource_obj.access() as r:
            [code block]...

        The resource resides in a 'resource box' thread and
        is only returned when it is not in use by another thread.

        Raises ResourceAccessTimeout if resource cant be retrieved
        within 1 second.
        """

        resource = self.request(timeout)
        
        try:
            yield resource
        finally:
            #only return it if you actually received it,
            self.return_()