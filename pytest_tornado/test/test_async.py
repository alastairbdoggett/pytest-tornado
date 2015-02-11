import functools
import pytest
from tornado import gen
from tornado.ioloop import TimeoutError
from decorator import decorator


@decorator
def _assert_raises(func, *args, **kwargs):
    with pytest.raises(ZeroDivisionError):
        func(*args, **kwargs)


@decorator
def _assert_times_out(func, *args, **kwargs):
    with pytest.raises(TimeoutError):
        func(*args, **kwargs)


@gen.coroutine
def dummy_coroutine(io_loop):
    yield gen.Task(io_loop.add_callback)
    raise gen.Return(True)


def test_explicit_start_and_stop(io_loop):
    future = dummy_coroutine(io_loop)
    future.add_done_callback(lambda *args: io_loop.stop())
    io_loop.start()
    assert future.result()


def test_run_sync(io_loop):
    dummy = functools.partial(dummy_coroutine, io_loop)
    finished = io_loop.run_sync(dummy)
    assert finished


@pytest.gen_test
def test_gen_test_sync(io_loop):
    assert True


@pytest.gen_test
def test_gen_test(io_loop):
    result = yield dummy_coroutine(io_loop)
    assert result


@_assert_raises
@pytest.gen_test
def test_gen_test_swallows_exceptions(io_loop):
    1 / 0


@_assert_raises
@pytest.gen_test
def test_gen_test_yields_forever(io_loop):
    yield dummy_coroutine(io_loop)
    # pytest uses generators to collect tests, so it will never make it here
    1 / 0


@pytest.gen_test()
def test_gen_test_callable(io_loop):
    result = yield dummy_coroutine(io_loop)
    assert result


@_assert_times_out
@pytest.gen_test(timeout=0.1)
def test_gen_test_with_timeout(io_loop):
    yield gen.Task(io_loop.add_timeout, io_loop.time() + 1)


def test_undecorated_generator(io_loop):
    with pytest.raises(ZeroDivisionError):
        yield gen.Task(io_loop.add_callback)
        1 / 0


def test_generators_implicitly_gen_test_marked(request, io_loop):
    yield gen.Task(io_loop.add_callback)
    assert 'gen_test' in request.keywords


@pytest.mark.gen_test
def test_explicit_gen_test_marker(request, io_loop):
    yield gen.Task(io_loop.add_callback)
    assert 'gen_test' in request.keywords


@pytest.mark.gen_test(timeout=0.5)
def test_gen_test_marker_with_params(request, io_loop):
    yield gen.Task(io_loop.add_callback)
    assert request.keywords['gen_test'].kwargs['timeout'] == 0.5
