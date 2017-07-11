import signal
import unittest

class TestHang(Exception):
    pass

def test_name(func):
     def inner(*args, **kwargs): 
         print ("\n******** STARTING TEST: %s *********" % func.__name__)
         return func(*args, **kwargs) 
     return inner

def count_spy(*args,**kwargs):
    cnt = 0
    while True:
        cnt = cnt + 1
        yield cnt

def test_hang_handler(signum, frame):
    raise TestHang

def set_test_hang_alarm(func):
    def inner(*args,**kwargs):
        signal.signal(signal.SIGALRM, test_hang_handler)
        signal.alarm(1)
        return func(*args,**kwargs)
    return inner

def clear_test_hang_alarm(func):
    def inner(*args,**kwargs):
        signal.alarm(0)
        return func(*args,**kwargs)
    return inner

def close_all_threads(func):
    def inner(self):
        try:
            return func(self)
        finally:
            [x.close() for x in self.threads_to_close]

    return inner

class GWTTestCase(unittest.TestCase):


    def GIVEN_expect(self,desc,e):
        self.expected = e

    def THEN_ExpectedActualMatch(self,desc):
        self.assertEqual(self.expected,self.actual)

    def THEN_exception_occurs(self,e):
        self.assertRaises(e,self.func_to_check['func'],
                          *self.func_to_check['args'],
                          *self.func_to_check['kwargs'])

