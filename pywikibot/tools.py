# -*- coding: utf-8  -*-
"""Miscellaneous helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2008
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'

import sys
import threading
import time
import inspect
import re
import collections
from distutils.version import Version

if sys.version_info[0] > 2:
    import queue as Queue
    basestring = (str,)
else:
    import Queue


# These variables are functions debug(str) and warning(str)
# which are initially the builtin print function.
# They exist here as the deprecators in this module rely only on them.
# pywikibot updates these function variables in bot.init_handlers()
debug = warning = print


def empty_iterator():
    # http://stackoverflow.com/a/13243870/473890
    """An iterator which does nothing."""
    return
    yield


class UnicodeMixin(object):

    """Mixin class to add __str__ method in Python 2 or 3."""

    if sys.version_info[0] > 2:
        def __str__(self):
            return self.__unicode__()
    else:
        def __str__(self):
            return self.__unicode__().encode('utf8')


# From http://python3porting.com/preparing.html
class ComparableMixin(object):

    """Mixin class to allow comparing to other objects which are comparable."""

    def __lt__(self, other):
        return other >= self._cmpkey()

    def __le__(self, other):
        return other > self._cmpkey()

    def __eq__(self, other):
        return other == self._cmpkey()

    def __ge__(self, other):
        return other < self._cmpkey()

    def __gt__(self, other):
        return other <= self._cmpkey()

    def __ne__(self, other):
        return other != self._cmpkey()


class MediaWikiVersion(Version):

    """Version object to allow comparing 'wmf' versions with normal ones."""

    MEDIAWIKI_VERSION = re.compile(r'(\d+(?:\.\d+)*)(?:wmf(\d+))?')

    def parse(self, vstring):
        version_match = MediaWikiVersion.MEDIAWIKI_VERSION.match(vstring)
        if not version_match:
            raise ValueError('Invalid version number')
        components = [int(n) for n in version_match.group(1).split('.')]
        self.wmf_version = None
        if version_match.group(2):  # wmf version
            self.wmf_version = int(version_match.group(2))
        self.version = tuple(components)

    def __str__(self):
        vstring = '.'.join(str(v) for v in self.version)
        if self.wmf_version:
            vstring += 'wmf{0}'.format(self.wmf_version)
        return vstring

    def _cmp(self, other):
        if isinstance(other, basestring):
            other = MediaWikiVersion(other)

        if self.version > other.version:
            return 1
        if self.version < other.version:
            return -1
        if self.wmf_version and other.wmf_version:
            if self.wmf_version > other.wmf_version:
                return 1
            if self.wmf_version < other.wmf_version:
                return -1
            return 0
        elif other.wmf_version:
            return 1
        elif self.wmf_version:
            return -1
        else:
            return 0

    if sys.version_info[0] == 2:
        __cmp__ = _cmp


class ThreadedGenerator(threading.Thread):

    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, I{not} self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread.  Example usage:

    >>> gen = ThreadedGenerator(target=range, args=(20,))
    >>> try:
    ...     data = list(gen)
    ... finally:
    ...     gen.stop()
    >>> data
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

    """

    def __init__(self, group=None, target=None, name="GeneratorThread",
                 args=(), kwargs=None, qsize=65536):
        """Constructor.  Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        @param qsize: The size of the lookahead queue. The larger the qsize,
        the more values will be computed in advance of use (which can eat
        up memory and processor time).
        @type qsize: int

        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, "generator"):
            raise RuntimeError("No generator for ThreadedGenerator to run.")
        self.args, self.kwargs = args, kwargs
        threading.Thread.__init__(self, group=group, name=name)
        self.queue = Queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.isAlive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.isSet():
            try:
                yield self.queue.get(True, 0.25)
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
        self.finished.set()

    def run(self):
        """Run the generator and store the results on the queue."""
        iterable = any([hasattr(self.generator, key)
                        for key in ['__iter__', '__getitem__']])
        if iterable and not self.args and not self.kwargs:
            self.__gen = self.generator
        else:
            self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.isSet():
                    return
                try:
                    self.queue.put_nowait(result)
                except Queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.isSet() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()


def itergroup(iterable, size):
    """Make an iterator that returns lists of (up to) size items from iterable.

    Example:

    >>> i = itergroup(range(25), 10)
    >>> print(next(i))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> print(next(i))
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    >>> print(next(i))
    [20, 21, 22, 23, 24]
    >>> print(next(i))
    Traceback (most recent call last):
     ...
    StopIteration

    """
    group = []
    for item in iterable:
        group.append(item)
        if len(group) == size:
            yield group
            group = []
    if group:
        yield group


class ThreadList(list):

    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the append()
    method.  If the maximum number of simultaneous threads has not been reached,
    the Thread object will be started immediately; if not, the append() call
    will block until the thread is able to start.

    >>> pool = ThreadList(limit=10)
    >>> def work():
    ...     time.sleep(1)
    ...
    >>> for x in range(20):
    ...     pool.append(threading.Thread(target=work))
    ...

    """

    _logger = "threadlist"

    def __init__(self, limit=128, *args):
        """Constructor."""
        self.limit = limit
        super(ThreadList, self).__init__(*args)
        for item in self:
            if not isinstance(threading.Thread, item):
                raise TypeError("Cannot add '%s' to ThreadList" % type(item))

    def active_count(self):
        """Return the number of alive threads, and delete all non-alive ones."""
        count = 0
        for item in self[:]:
            if item.isAlive():
                count += 1
            else:
                self.remove(item)
        return count

    def append(self, thd):
        """Add a thread to the pool and start it."""
        if not isinstance(thd, threading.Thread):
            raise TypeError("Cannot append '%s' to ThreadList" % type(thd))
        while self.active_count() >= self.limit:
            time.sleep(2)
        super(ThreadList, self).append(thd)
        thd.start()

    def stop_all(self):
        """Stop all threads the pool."""
        if self:
            debug(u'EARLY QUIT: Threads: %d' % len(self), ThreadList._logger)
        for thd in self:
            thd.stop()
            debug(u'EARLY QUIT: Queue size left in %s: %s'
                  % (thd, thd.queue.qsize()), ThreadList._logger)


def intersect_generators(genlist):
    """
    Intersect generators listed in genlist.

    Yield items only if they are yielded by all generators in genlist.
    Threads (via ThreadedGenerator) are used in order to run generators
    in parallel, so that items can be yielded before generators are
    exhausted.

    Threads are stopped when they are either exhausted or Ctrl-C is pressed.
    Quitting before all generators are finished is attempted if
    there is no more chance of finding an item in all queues.

    @param genlist: list of page generators
    @type genlist: list
    """
    _logger = ""

    # Item is cached to check that it is found n_gen
    # times before being yielded.
    cache = collections.defaultdict(set)
    n_gen = len(genlist)

    # Class to keep track of alive threads.
    # Start new threads and remove completed threads.
    thrlist = ThreadList()

    for source in genlist:
        threaded_gen = ThreadedGenerator(name=repr(source), target=source)
        thrlist.append(threaded_gen)
        debug("INTERSECT: thread started: %r" % threaded_gen, _logger)

    while True:
        # Get items from queues in a round-robin way.
        for t in thrlist:
            try:
                # TODO: evaluate if True and timeout is necessary.
                item = t.queue.get(True, 0.1)

                # Cache entry is a set of tuples (item, thread).
                # Duplicates from same thread are not counted twice.
                cache[item].add((item, t))
                if len(cache[item]) == n_gen:
                    yield item
                    # Remove item from cache.
                    # No chance of seeing it again (see later: early stop).
                    cache.pop(item)

                active = thrlist.active_count()
                max_cache = n_gen
                if cache.values():
                    max_cache = max(len(v) for v in cache.values())
                # No. of active threads is not enough to reach n_gen.
                # We can quit even if some thread is still active.
                # There could be an item in all generators which has not yet
                # appeared from any generator. Only when we have lost one
                # generator, then we can bail out early based on seen items.
                if active < n_gen and n_gen - max_cache > active:
                    thrlist.stop_all()
                    return
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                thrlist.stop_all()
            finally:
                # All threads are done.
                if thrlist.active_count() == 0:
                    return


class CombinedError(KeyError, IndexError):

    """An error that gets caught by both KeyError and IndexError."""


class EmptyDefault(str, collections.Mapping):

    """
    A default for a not existing siteinfo property.

    It should be chosen if there is no better default known. It acts like an
    empty collections, so it can be iterated through it savely if treated as a
    list, tuple, set or dictionary. It is also basically an empty string.

    Accessing a value via __getitem__ will result in an combined KeyError and
    IndexError.
    """

    def __init__(self):
        """Initialise the default as an empty string."""
        str.__init__(self)

    def _empty_iter(self):
        """An iterator which does nothing and drops the argument."""
        return empty_iterator()

    def __getitem__(self, key):
        """Raise always a L{CombinedError}."""
        raise CombinedError(key)

    iteritems = itervalues = iterkeys = __iter__ = _empty_iter


EMPTY_DEFAULT = EmptyDefault()


class SelfCallMixin(object):

    """Return self when called."""

    def __call__(self):
        return self


class SelfCallDict(SelfCallMixin, dict):

    """Dict with SelfCallMixin."""


class SelfCallString(SelfCallMixin, str):

    """Unicode string with SelfCallMixin."""


class DequeGenerator(collections.deque):

    """A generator that allows items to be added during generating."""

    def __iter__(self):
        """Return the object which will be iterated."""
        return self

    def next(self):
        """Python 3 iterator method."""
        if len(self):
            return self.popleft()
        else:
            raise StopIteration

    def __next__(self):
        """Python 3 iterator method."""
        return self.next()

# Decorators
#
# Decorator functions without parameters are _invoked_ differently from
# decorator functions with function syntax.  For example, @deprecated causes
# a different invocation to @deprecated().

# The former is invoked with the decorated function as args[0].
# The latter is invoked with the decorator arguments as *args & **kwargs,
# and it must return a callable which will be invoked with the decorated
# function as args[0].

# The follow deprecators may support both syntax, e.g. @deprecated and
# @deprecated() both work.  In order to achieve that, the code inspects
# args[0] to see if it callable.  Therefore, a decorator must not accept
# only one arg, and that arg be a callable, as it will be detected as
# a deprecator without any arguments.


def add_decorated_full_name(obj):
    """Extract full object name, including class, and store in __full_name__.

    This must be done on all decorators that are chained together, otherwise
    the second decorator will have the wrong full name.

    @param obj: A object being decorated
    @type obj: object
    """
    if hasattr(obj, '__full_name__'):
        return
    # The current frame is add_decorated_full_name
    # The next frame is the decorator
    # The next frame is the object being decorated
    frame = inspect.currentframe().f_back.f_back
    class_name = frame.f_code.co_name
    if class_name and class_name != '<module>':
        obj.__full_name__ = (obj.__module__ + '.' +
                             class_name + '.' +
                             obj.__name__)
    else:
        obj.__full_name__ = (obj.__module__ + '.' +
                             obj.__name__)


def add_full_name(obj):
    """
    A decorator to add __full_name__ to the function being decorated.

    This should be done for all decorators used in pywikibot, as any
    decorator that does not add __full_name__ will prevent other
    decorators in the same chain from being able to obtain it.

    This can be used to monkey-patch decorators in other modules.
    e.g.
    <xyz>.foo = add_full_name(<xyz>.foo)

    @param obj: The function to decorate
    @type obj: callable
    @return: decorating function
    @rtype: function
    """
    def outer_wrapper(*outer_args, **outer_kwargs):
        """Outer wrapper.

        The outer wrapper may be the replacement function if the decorated
        decorator was called without arguments, or the replacement decorator
        if the decorated decorator was called without arguments.

        @param outer_args: args
        @type outer_args: list
        @param outer_kwargs: kwargs
        @type: outer_kwargs: dict
        """
        def inner_wrapper(*args, **kwargs):
            """Replacement function.

            If the decorator supported arguments, they are in outer_args,
            and this wrapper is used to process the args which belong to
            the function that the decorated decorator was decorating.

            @param args: args passed to the decorated function.
            @param kwargs: kwargs passed to the decorated function.
            """
            add_decorated_full_name(args[0])
            return obj(*outer_args, **outer_kwargs)(*args, **kwargs)

        inner_wrapper.__doc__ = obj.__doc__
        inner_wrapper.__name__ = obj.__name__
        inner_wrapper.__module__ = obj.__module__

        # The decorator being decorated may have args, so both
        # syntax need to be supported.
        if (len(outer_args) == 1 and len(outer_kwargs) == 0 and
                callable(outer_args[0])):
            add_decorated_full_name(outer_args[0])
            return obj(outer_args[0])
        else:
            return inner_wrapper

    return outer_wrapper


@add_full_name
def deprecated(*args, **kwargs):
    """Decorator to output a deprecation warning.

    @kwarg instead: if provided, will be used to specify the replacement
    @type instead: string
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*args, **kwargs):
            """Replacement function.

            @param args: args passed to the decorated function.
            @type args: list
            @param kwargs: kwargs passed to the decorated function.
            @type kwargs: dict
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            if instead:
                warning(u"%s is deprecated, use %s instead." % (name, instead))
            else:
                warning(u"%s is deprecated." % (name))
            return obj(*args, **kwargs)

        wrapper.__doc__ = obj.__doc__
        wrapper.__name__ = obj.__name__
        wrapper.__module__ = obj.__module__
        return wrapper

    without_parameters = len(args) == 1 and len(kwargs) == 0 and callable(args[0])
    if 'instead' in kwargs:
        instead = kwargs['instead']
    elif not without_parameters and len(args) == 1:
        instead = args[0]
    else:
        instead = False

    # When called as @deprecated, return a replacement function
    if without_parameters:
        return decorator(args[0])
    # Otherwise return a decorator, which returns a replacement function
    else:
        return decorator


def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg."""
    return deprecated_args(**{old_arg: new_arg})


def deprecated_args(**arg_pairs):
    """
    Decorator to declare multiple args deprecated.

    @param arg_pairs: Each entry points to the new argument name. With True or
        None it drops the value and prints a warning. If False it just drops
        the value.
    """
    _logger = ""

    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            @param __args: args passed to the decorated function
            @type __args: list
            @param __kwargs: kwargs passed to the decorated function
            @type __kwargs: dict
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            for old_arg, new_arg in arg_pairs.items():
                if old_arg in __kw:
                    if new_arg not in [True, False, None]:
                        if new_arg in __kw:
                            warning(u"%(new_arg)s argument of %(name)s "
                                    "replaces %(old_arg)s; cannot use both."
                                    % locals())
                        else:
                            # If the value is positionally given this will
                            # cause a TypeError, which is intentional
                            warning(u"%(old_arg)s argument of %(name)s "
                                    "is deprecated; use %(new_arg)s instead."
                                    % locals())
                            __kw[new_arg] = __kw[old_arg]
                    elif new_arg is not False:
                        debug(u"%(old_arg)s argument of %(name)s is "
                              "deprecated." % locals(), _logger)
                    del __kw[old_arg]
            return obj(*__args, **__kw)

        wrapper.__doc__ = obj.__doc__
        wrapper.__name__ = obj.__name__
        wrapper.__module__ = obj.__module__
        if not hasattr(obj, '__full_name__'):
            add_decorated_full_name(obj)
        wrapper.__full_name__ = obj.__full_name__
        return wrapper
    return decorator


def py3_parent_qualname(obj):
    """Return parent qualname."""
    (normal, sep, local) = obj.__qualname__.partition('.<locals>')
    if local:
        return normal
    else:
        normal.rsplit('.', 1)[0]


def class_qualname(meth):
    """Return class qualname."""
    if sys.version_info[0] == 3:
        if 'decorator' in meth.__qualname__:
            return None
        return meth.__qualname__.partition(
            '.<locals>')[0].rsplit('.', 1)[0]
    else:
        if hasattr(meth, 'im_class'):
            return meth.im_class.__name__
        else:
            return None


def get_method_class(meth):
    if sys.version_info[0] == 2:
        if hasattr(meth, '__self__'):
            if meth.__self__:
                return meth.__self__
        if hasattr(meth, 'im_class'):
            return meth.im_class

    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__

    name = class_qualname(meth)

    if name and inspect.isfunction(meth):
        if hasattr(meth, '__module__'):
            module = sys.modules[meth.__module__]
        else:
            module = inspect.getmodule(meth)

        cls = getattr(module, name)
        if isinstance(cls, type):
            return cls


def get_scoped_function_name(obj, func):
    """Find the name used for a function within an object."""
    o = [name for name, value in obj.__dict__.items() if value == func]
    if o:
        return o[0]


def redirect_func(target, cls=None,
                  source_module=None, target_module=None,
                  old_name=None, class_name=None):
    """
    Return a function which can be used to redirect to 'target'.

    It also acts like marking that function deprecated and copies all
    parameters.

    @param target: The targeted function which is to be executed.
    @type target: callable
    @param source_module: The module of the old function. If '.' defaults
        to target_module. If 'None' (default) it tries to guess it from the
        executing function.
    @type source_module: basestring
    @param target_module: The module of the target function. If
        'None' (default) it tries to get it from the target. Might not work
        with nested classes.
    @type target_module: basestring
    @param old_name: The old function name. If None it uses the name of the
        new function.
    @type old_name: basestring
    @param class_name: The name of the class. It's added to the target and
        source module (separated by a '.').
    @type class_name: basestring
    @return: A new function which adds a warning prior to each execution.
    @rtype: callable
    """
    def call(*a, **kw):
        target_cls = cls
        if hasattr(target, '__full_name__'):
            call.__target_full_name__ = target.__full_name__
        if not hasattr(call, '__target_full_name__'):
            if sys.version_info[0] == 3:
                target_parts = (target.__module__, target.__qualname__)
            else:
                if not target_cls:
                    target_cls = get_method_class(target)

                if target_cls:
                    target_parts = (target.__module__, target_cls.__name__,
                                    target.__name__)
                else:
                    target_parts = (target.__module__, target.__name__)

            call.__target_full_name__ = '.'.join(target_parts)

        source_name = None
        if not hasattr(call, '__full_name__'):
            source_parts = None

            if not target_cls:
                target_cls = get_method_class(target)

            # Find this inner function within the target class
            if isinstance(target_cls, type):
                source_name = get_scoped_function_name(target_cls, call)
                if source_name:
                    source_parts = (source_module, target_cls.__name__,
                                    source_name)

            # Find this inner function within the target module
            else:
                module = sys.modules[source_module]
                source_name = get_scoped_function_name(module, call)
                if source_name:
                    source_parts = (source_module, source_name)

            if source_parts:
                call.__full_name__ = '.'.join(source_parts)
            else:
                call.__full_name__ = '<unknown>'

        warning(('{source_name} is DEPRECATED, use {target_name} '
                 'instead.').format(source_name=call.__full_name__,
                                    target_name=call.__target_full_name__))

        if target_cls:
            static_method = False
            class_method = False

            if sys.version_info[0] == 3:
                target_cls_obj = object.__getattribute__(target_cls, target.__name__)
                if hasattr(target_cls_obj, '__func__'):
                    static_method = target_cls_obj.__func__ == target
                if (hasattr(target, '__func__') and
                        hasattr(target_cls_obj, '__func__')):
                    class_method = target_cls_obj.__func__ == target.__func__
            else:
                if hasattr(target, '__self__'):
                    class_method = target.__self__ is target_cls
                static_method = inspect.isfunction(target)

            # The args for static and class methods are populated with
            # the class, which needs to be removed as target is already
            # bound to a specific object.
            if static_method or class_method:
                a = a[1:]

        return target(*a, **kw)

    source_module = sys._getframe(1).f_globals['__name__']

    return call


class DeprecationWrapper(object):

    """A wrapper to deprecate attributes and items of it."""

    def __init__(self, obj):
        """
        Initialise the wrapper.

        @param obj: The object instance
        @type obj: object
        """
        super(DeprecationWrapper, self).__setattr__('_deprecated', {})
        super(DeprecationWrapper, self).__setattr__('_obj', obj)
        if hasattr(obj, '__doc__'):
            super(DeprecationWrapper, self).__setattr__(
                '__doc__', obj.__doc__)

    def _add_deprecated_name(self, name, replacement=None,
                             replacement_name=None):
        """
        Add the name to the local deprecated names dict.

        @param name: The name of the deprecated class, variable, etc.
             It may not be already deprecated.
        @type name: str
        @param replacement: The replacement value which should be returned
            instead. If the name is already an attribute of that module this
            must be None. If None it'll return the attribute of the module.
        @type replacement: any
        @param replacement_name: The name of the new replaced value. Required
            if C{replacement} is not None and it has no __name__ attribute.
        @type replacement_name: str
        """
        if '.' in name:
            raise ValueError('Deprecated name "{0}" may not contain '
                             '".".'.format(name))
        if name in self._deprecated:
            raise ValueError('Name "{0}" is already deprecated.'.format(name))
        if replacement is not None and hasattr(self._obj, name):
            raise ValueError('Object already has an attribute named '
                             '"{0}".'.format(name))
        if (replacement and not replacement_name
                and hasattr(replacement, '__module__')):
            if hasattr(replacement, '__name__'):
                replacement_name = replacement.__module__
                if hasattr(replacement, '__self__'):
                    replacement_name += '.'
                    replacement_name += replacement.__self__.__class__.__name__
                replacement_name += '.' + replacement.__name__
        if replacement_name is None:
            raise TypeError('Replacement must have a __name__ attribute '
                            'or a replacement name must be set '
                            'specifically.')
        if isinstance(self._obj, list):
            name = int(name)
        self._deprecated[name] = (replacement_name, replacement)
        if self._obj.__class__.__name__ == 'type':
            def wrapper(*args, **kwargs):
                return self._get_deprecated(name)(*args, **kwargs)

            setattr(self, name, wrapper)

    # FIXME: unnecessary, but here to reduce the chance of conflicts.
    # Remove all instances before merge.
    _add_deprecated_attr = _add_deprecated_name

    def _get_deprecated(self, attr):
        """Helper function to issue a warning and return the alternative."""
        if attr in self._deprecated:
            if self._deprecated[attr][0]:
                name = "[object]"
                if hasattr(self._obj, '__name__'):
                    name = self._obj.__name__
                warning(u"{0}.{1} is DEPRECATED, use {2} instead.".format(
                        name, attr,
                        self._deprecated[attr][0]))
                if self._deprecated[attr][1]:
                    return self._deprecated[attr][1]
            else:
                warning(u"{0}.{1} is DEPRECATED.".format(
                        self._obj.__name__, attr))

    def __setattr__(self, attr, value):
        """Set the value in the wrapped obj."""
        setattr(self._obj, attr, value)

    def __getattr__(self, attr):
        """Return the attribute with a deprecation warning if required."""
        rv = self._get_deprecated(attr)
        if rv:
            return rv
        return getattr(self._obj, attr)

    def __setitem__(self, key, value):
        """Set the value in the wrapped obj."""
        self._obj[key] = value

    def __getitem__(self, key):
        """Return the item with a deprecation warning if required."""
        if key in self._deprecated:
            if self._deprecated[key][0]:
                warning(u"Accessing this {0} using [{1}] is DEPRECATED, use [{2}] instead.".format(
                        self._obj.__class__.__name__, repr(key),
                        repr(self._deprecated[key][0])))
                if self._deprecated[key][1]:
                    return self._deprecated[key][1]
            else:
                warning(u"Accessing this {0} using[{1}] is DEPRECATED.".format(
                        self._obj.__name__, repr(key)))
        rv = self._obj[key]
        return rv

    def __getattribute__(self, attr):
        """Wrap the object."""
        if attr in ['__dict__', '__class__']:
            return self._obj.__getattribute__(attr)
        try:
            retval = object.__getattribute__(self, attr)
        except AttributeError:
            if self._obj.__class__.__name__ == 'type':
                retval = self._obj.__dict__[attr]
            else:
                retval = self._obj.__getattribute__(attr)
        return retval

    def __call__(self, *args, **kwargs):
        """ Wrap the object. """
        if self._obj.__class__.__name__ == 'type':
            rv = self._obj(*args, **kwargs)
            return rv

    def __contains__(self, key):
        """ Wrap the object. """
        return key in self._obj


class ModuleDeprecationWrapper(DeprecationWrapper):

    """A wrapper for a module to deprecate classes or variables of it."""

    def __init__(self, module):
        """
        Initialise the wrapper.

        It will automatically overwrite the module with this instance in
        C{sys.modules}.

        @param module: The module name or instance
        @type module: str or module
        """
        if isinstance(module, basestring):
            module = sys.modules[module]
        super(ModuleDeprecationWrapper, self).__init__(module)
        sys.modules[module.__name__] = self


if __name__ == "__main__":
    def _test():
        import doctest
        doctest.testmod()
    _test()
