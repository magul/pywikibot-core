# -*- coding: utf-8  -*-
"""Tests for deprecation tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.tools import (
    add_full_name,
    deprecated, deprecate_arg, deprecated_args,
    redirect_func,
    DeprecationWrapper,
)

from tests.aspects import unittest, DeprecationTestCase, TestCase


@add_full_name
def noop(foo=None):
    """Dummy decorator."""
    def decorator(obj):
        def wrapper(*args, **kwargs):
            raise Exception(obj.__full_name__)
            return obj(*args, **kwargs)
        return wrapper
    return decorator


@add_full_name
def noop2():
    """Dummy decorator."""
    def decorator(obj):
        def wrapper(*args, **kwargs):
            raise Exception(obj.__full_name__)
            return obj(*args, **kwargs)
        return wrapper
    return decorator


@noop()
def decorated_func():
    """Test dummy decorator."""
    pass


@noop(foo='bar')
def decorated_func2():
    """Test dummy decorator."""
    pass


@noop('baz')
def decorated_func3():
    """Test dummy decorator."""
    pass


class DecoratorFullNameTestCase(TestCase):

    """Class with methods deprecated."""

    net = False

    def test_add_full_name_decorator(self):
        self.assertRaisesRegex(
            Exception,
            __name__ + '.decorated_func',
            decorated_func)
        self.assertRaisesRegex(
            Exception,
            __name__ + '.decorated_func2',
            decorated_func2)
        self.assertRaisesRegex(
            Exception,
            __name__ + '.decorated_func3',
            decorated_func3)


@deprecated()
def deprecated_func(foo=None):
    """Deprecated function."""
    return foo


@deprecated
def deprecated_func2(foo=None):
    """Deprecated function."""
    return foo


@deprecated(instead='baz')
def deprecated_func_instead(foo=None):
    """Deprecated function."""
    return foo


@deprecated()
def deprecated_func_bad_args(self):
    """Deprecated function with arg 'self'."""
    return self


@deprecate_arg('bah', 'foo')
def deprecated_func_arg(foo=None):
    """Deprecated arg 'bah'."""
    return foo


@deprecated_args(bah='foo')
def deprecated_func_arg2(foo=None):
    """Test deprecated_args with one rename."""
    return foo


@deprecated_args(bah='foo', silent=False, loud=True, old=None)
def deprecated_func_arg3(foo=None):
    """Test deprecated_args with three drops and one rename."""
    return foo


class DeprecatedMethodClass(object):

    """Class with methods deprecated."""

    @classmethod
    @deprecated()
    def class_method(cls, foo=None):
        return foo

    @staticmethod
    @deprecated()
    def static_method(foo=None):
        return foo

    @deprecated()
    def instance_method(self, foo=None):
        self.foo = foo
        return foo

    @deprecated
    def instance_method2(self, foo=None):
        self.foo = foo
        return foo

    def undecorated_method(self, foo=None):
        return foo

    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_arg(self, foo=None):
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecate_arg('bah2', 'foo2')
    def deprecated_instance_method_args(self, foo, foo2):
        self.foo = foo
        self.foo2 = foo2
        return (foo, foo2)

    @deprecated()
    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_and_arg(self, foo):
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecated()
    def deprecated_instance_method_and_arg2(self, foo):
        self.foo = foo
        return foo


@deprecated()
class DeprecatedClassNoInit(object):

    """Deprecated class."""

    pass


@deprecated()
class DeprecatedClass(object):

    """Deprecated class."""

    def __init__(self, foo=None):
        self.foo = foo


class NormalClass(object):

    """Normal class."""

    def bar(self):
        return 'bar'


class ClassWithRedirectedMethod(object):

    """Normal class with a redirected method added in a test."""

    @classmethod
    def class_bar(cls):
        return 'bar'

    @staticmethod
    def static_bar():
        return 'bar'

    def bar(self):
        return 'bar'

    def baz(self):
        return 'baz'


def normal_function():
    return 'bar'


RedirectedClass = None
redirected_function = None


class DeprecatorDecoratorTestCase(DeprecationTestCase):

    """Test cases for deprecation tools."""

    net = False

    def test_deprecated_function_zero_arg(self):
        """Test @deprecated with functions, with zero arguments."""
        rv = deprecated_func()
        self.assertEqual(rv, None)
        self.assertDeprecation(
            __name__ + '.deprecated_func is deprecated.')

    def test_deprecated_function(self):
        """Test @deprecated with functions."""
        rv = deprecated_func('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(
            __name__ + '.deprecated_func is deprecated.')

        self._reset_messages()

        rv = deprecated_func(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation(
            __name__ + '.deprecated_func is deprecated.')

    def test_deprecated_function2(self):
        """Test @deprecated with functions."""
        rv = deprecated_func2('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(
            __name__ + '.deprecated_func2 is deprecated.')

        self._reset_messages()

        rv = deprecated_func2(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation(
            __name__ + '.deprecated_func2 is deprecated.')

    def test_deprecated_function_instead(self):
        """Test @deprecated with functions, using instead."""
        rv = deprecated_func_instead('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(
            __name__ + '.deprecated_func_instead is deprecated, use baz instead.')

    def test_deprecated_function_bad_args(self):
        rv = deprecated_func_bad_args(None)
        self.assertEqual(rv, None)
        self.assertDeprecation(
            __name__ + '.deprecated_func_bad_args is deprecated.')

        self._reset_messages()

        rv = deprecated_func_bad_args('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(
            __name__ + '.deprecated_func_bad_args is deprecated.')

        self._reset_messages()

        rv = deprecated_func_bad_args(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation(
            __name__ + '.deprecated_func_bad_args is deprecated.')

        self._reset_messages()

        f = DeprecatedMethodClass()
        rv = deprecated_func_bad_args(f)
        self.assertEqual(rv, f)
        self.assertDeprecation(
            __name__ + '.deprecated_func_bad_args is deprecated.')

    def test_deprecated_instance_method(self):
        f = DeprecatedMethodClass()

        rv = f.instance_method()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.instance_method is deprecated.')

        self._reset_messages()

        rv = f.instance_method('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.instance_method is deprecated.')

        self._reset_messages()

        rv = f.instance_method(1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.instance_method is deprecated.')

    #@unittest.expectedFailure
    def test_deprecated_instance_method2(self):
        f = DeprecatedMethodClass()

        rv = f.instance_method2()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.instance_method2 is deprecated.')

    def test_deprecated_class_method(self):
        """Test @deprecated with class methods."""
        rv = DeprecatedMethodClass.class_method()
        self.assertEqual(rv, None)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.class_method is deprecated.')

        self._reset_messages()

        rv = DeprecatedMethodClass.class_method('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.class_method is deprecated.')

        self._reset_messages()

        rv = DeprecatedMethodClass.class_method(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.class_method is deprecated.')

    def test_deprecated_static_method_zero_args(self):
        """Test @deprecated with static methods, with zero arguments."""
        rv = DeprecatedMethodClass.static_method()
        self.assertEqual(rv, None)
        self.assertDeprecation(__name__ + '.DeprecatedMethodClass.static_method is deprecated.')

    def test_deprecated_static_method(self):
        """Test @deprecated with static methods."""
        rv = DeprecatedMethodClass.static_method('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation(__name__ + '.DeprecatedMethodClass.static_method is deprecated.')

        self._reset_messages()

        rv = DeprecatedMethodClass.static_method(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation(__name__ + '.DeprecatedMethodClass.static_method is deprecated.')

    def test_deprecate_class_zero_arg(self):
        """Test @deprecated with classes, without arguments."""
        df = DeprecatedClassNoInit()
        self.assertEqual(df.__doc__, 'Deprecated class.')
        self.assertDeprecation(__name__ + '.DeprecatedClassNoInit is deprecated.')

        self._reset_messages()

        df = DeprecatedClass()
        self.assertEqual(df.foo, None)
        self.assertDeprecation(__name__ + '.DeprecatedClass is deprecated.')

    def test_deprecate_class(self):
        """Test @deprecated with classes."""
        df = DeprecatedClass('a')
        self.assertEqual(df.foo, 'a')
        self.assertDeprecation(__name__ + '.DeprecatedClass is deprecated.')

    def test_deprecate_function_arg(self):
        def tests(func):
            rv = func()
            self.assertEqual(rv, None)
            self.assertNoDeprecation()

            rv = func('a')
            self.assertEqual(rv, 'a')
            self.assertNoDeprecation()

            rv = func(bah='b')
            self.assertEqual(rv, 'b')
            self.assertDeprecation('bah argument of ' + __name__ + '.' + func.__name__ + ' is deprecated; use foo instead.')

            self._reset_messages()

            rv = func(foo=1)
            self.assertEqual(rv, 1)
            self.assertNoDeprecation()

            self.assertRaisesRegex(
                TypeError,
                r"deprecated_func_arg2?\(\) got multiple values for (keyword )?argument 'foo'",
                func,
                'a', bah='b'
            )
            self._reset_messages()

        tests(deprecated_func_arg)
        tests(deprecated_func_arg2)

    def test_deprecate_and_remove_function_args(self):
        rv = deprecated_func_arg3()
        self.assertEqual(rv, None)
        self.assertNoDeprecation()

        rv = deprecated_func_arg3(foo=1, silent=42)
        self.assertEqual(rv, 1)
        self.assertNoDeprecation()

        rv = deprecated_func_arg3(2)
        self.assertEqual(rv, 2)
        self.assertNoDeprecation()

        rv = deprecated_func_arg3(3, loud='3')
        self.assertEqual(rv, 3)
        self.assertDeprecation('loud argument of ' + __name__ + '.deprecated_func_arg3 is deprecated.')

        self._reset_messages()

        rv = deprecated_func_arg3(4, old='4')
        self.assertEqual(rv, 4)
        self.assertDeprecation('old argument of ' + __name__ + '.deprecated_func_arg3 is deprecated.')

        self._reset_messages()

    def test_deprecated_instance_method_zero_arg(self):
        """Test @deprecate_arg with classes, without arguments."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_arg()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertNoDeprecation()

    def test_deprecated_instance_method_arg(self):
        """Test @deprecate_arg with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_arg('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertNoDeprecation()

        rv = f.deprecated_instance_method_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_arg is deprecated; use foo instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertNoDeprecation()

    def test_deprecated_instance_method_args(self):
        """Test @deprecate_arg with instance methods and two args."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_args('a', 'b')
        self.assertEqual(rv, ('a', 'b'))
        self.assertNoDeprecation()

        rv = f.deprecated_instance_method_args(bah='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertDeprecation(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo2 instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_args(foo='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertNoDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertDeprecation(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo2 instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_args(foo2='c', bah='b')
        self.assertEqual(rv, ('b', 'c'))
        self.assertDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertNoDeprecation(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_args is deprecated; use foo2 instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_args(foo=1, foo2=2)
        self.assertEqual(rv, (1, 2))
        self.assertNoDeprecation()

    def test_deprecated_instance_method_and_arg(self):
        """Test @deprecate_arg and @deprecated with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated.')
        self.assertNoDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated; use foo instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated.')
        self.assertDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated; use foo instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated.')
        self.assertNoDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg is deprecated; use foo instead.')

    def test_deprecated_instance_method_and_arg2(self):
        """Test @deprecated and @deprecate_arg with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg2('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated.')
        self.assertNoDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated; use foo instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg2(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated.')
        self.assertDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated; use foo instead.')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg2(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation(
            __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated.')
        self.assertNoDeprecation(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2 is deprecated; use foo instead.')


class DeprecatorRedirectTestCase(DeprecationTestCase):

    """Test cases for deprecation redirector."""

    net = False

    def test_redirected_class(self):
        global RedirectedClass
        RedirectedClass = redirect_func(NormalClass)

        d = RedirectedClass()

        self.assertIsInstance(d, NormalClass)
        self.assertEqual(d.bar(), 'bar')

        self.assertDeprecation(__name__ + ".RedirectedClass is DEPRECATED, use " + __name__ + ".NormalClass instead.")

        self.assertTrue(hasattr(RedirectedClass, '__full_name__'))

    def test_redirected_classmethod(self):
        ClassWithRedirectedMethod.class_foo = redirect_func(ClassWithRedirectedMethod.class_bar)

        d = ClassWithRedirectedMethod()

        self.assertEqual(d.class_foo(), 'bar')

        self.assertDeprecation(__name__ + ".ClassWithRedirectedMethod.class_foo is DEPRECATED, use " + __name__ + ".ClassWithRedirectedMethod.class_bar instead.")

        self.assertTrue(hasattr(ClassWithRedirectedMethod.class_foo, '__full_name__'))

    def test_redirected_instancemethod(self):
        ClassWithRedirectedMethod.foo = redirect_func(ClassWithRedirectedMethod.bar)
        ClassWithRedirectedMethod.foz = redirect_func(ClassWithRedirectedMethod.baz)

        d = ClassWithRedirectedMethod()

        self.assertEqual(d.foo(), 'bar')
        self.assertEqual(d.foz(), 'baz')

        self.assertDeprecation(__name__ + ".ClassWithRedirectedMethod.foo is DEPRECATED, use " + __name__ + ".ClassWithRedirectedMethod.bar instead.")
        self.assertDeprecation(__name__ + ".ClassWithRedirectedMethod.foz is DEPRECATED, use " + __name__ + ".ClassWithRedirectedMethod.baz instead.")

        self.assertTrue(hasattr(ClassWithRedirectedMethod.foo, '__full_name__'))
        self.assertTrue(hasattr(ClassWithRedirectedMethod.foz, '__full_name__'))

    def test_redirected_staticmethod(self):
        ClassWithRedirectedMethod.static_foo = redirect_func(ClassWithRedirectedMethod.static_bar, cls=ClassWithRedirectedMethod)

        d = ClassWithRedirectedMethod()

        self.assertEqual(d.static_foo(), 'bar')

        self.assertDeprecation(__name__ + ".ClassWithRedirectedMethod.static_foo is DEPRECATED, use " + __name__ + ".ClassWithRedirectedMethod.static_bar instead.")

        self.assertTrue(hasattr(ClassWithRedirectedMethod.static_foo, '__full_name__'))

    def test_redirected_function(self):
        global redirected_function
        redirected_function = redirect_func(normal_function)

        self.assertEqual(redirected_function(), 'bar')

        self.assertDeprecation(__name__ + ".redirected_function is DEPRECATED, use " + __name__ + ".normal_function instead.")

        self.assertTrue(hasattr(redirected_function, '__full_name__'))


class DeprecatorWrapperTestCase(DeprecationTestCase):

    """Test cases for deprecation wrappers."""

    net = False

    def test_wrapped_class_instance(self):
        d = NormalClass()
        w = DeprecationWrapper(d)
        self.assertIsInstance(w, DeprecationWrapper)
        self.assertIsInstance(w, NormalClass)

        w._add_deprecated_name('foo', d.bar)
        self.assertEqual(w.foo(), 'bar')
        self.assertDeprecation("[object].foo is DEPRECATED, use " + __name__ + ".NormalClass.bar instead.")

    def test_wrapped_dict(self):
        d = {'a': 2, 'b': 3}
        w = DeprecationWrapper(d)
        self.assertIsInstance(w, DeprecationWrapper)
        self.assertIsInstance(w, dict)

        w._add_deprecated_name('a', d['b'], 'b')
        self.assertEqual(w['a'], 3)
        self.assertDeprecation("Accessing this dict using ['a'] is DEPRECATED, use ['b'] instead.")

    def test_wrapped_list(self):
        d = ['a', 'b']
        w = DeprecationWrapper(d)
        self.assertIsInstance(w, DeprecationWrapper)
        self.assertIsInstance(w, list)

        w._add_deprecated_name('0', d[1], 1)
        self.assertEqual(w[0], 'b')
        self.assertDeprecation("Accessing this list using [0] is DEPRECATED, use [1] instead.")


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
