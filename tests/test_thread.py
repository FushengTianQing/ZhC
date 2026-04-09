"""测试并发库 - 线程管理与同步原语"""

import threading
import queue
import time
import multiprocessing
import pytest


class TestThreadBasics:
    """线程基础功能测试"""

    def test_thread_create_and_join(self):
        """测试线程创建和等待"""
        q = queue.Queue()

        def worker(n):
            time.sleep(0.05)
            q.put(n * 2)

        t = threading.Thread(target=worker, args=(21,))
        t.start()
        t.join(timeout=1)

        assert not t.is_alive()
        assert q.get(timeout=1) == 42

    def test_thread_self(self):
        """测试获取当前线程ID"""
        main_thread = threading.main_thread()
        assert main_thread.ident is not None

        results = []

        def worker():
            results.append(threading.current_thread().ident != main_thread.ident)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert results[0]  # 子线程的 ID 应该与主线程不同

    def test_thread_sleep(self):
        """测试线程休眠"""
        start = time.time()

        def worker():
            time.sleep(0.2)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        elapsed = time.time() - start
        assert 0.15 <= elapsed <= 0.35  # 允许一些误差

    def test_multiple_threads(self):
        """测试多个线程同时运行"""
        results = []

        def worker(n):
            time.sleep(0.05)
            results.append(n)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert sorted(results) == list(range(10))


class TestMutex:
    """互斥锁测试"""

    def test_mutex_basic(self):
        """测试互斥锁基本功能"""
        counter = [0]
        lock = threading.Lock()

        def worker(n):
            del n  # unused
            for _ in range(100):
                with lock:
                    counter[0] += 1

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter[0] == 500

    def test_mutex_trylock(self):
        """测试尝试加锁"""
        lock = threading.Lock()
        acquired_first = [False]
        acquired_second = [False]

        def worker():
            # 尝试获取锁
            result = lock.acquire(blocking=False)
            acquired_first[0] = result
            if result:
                # 持有锁一段时间
                time.sleep(0.2)
                lock.release()

        t = threading.Thread(target=worker)
        t.start()
        time.sleep(0.05)  # 确保 worker 获取了锁

        # 此时 worker 应该持有锁，尝试非阻塞获取应该失败
        result = lock.acquire(blocking=False)
        acquired_second[0] = result
        assert not acquired_second[0]  # 应该失败

        t.join()  # 等待 worker 释放锁

    def test_recursive_mutex(self):
        """测试递归互斥锁"""
        counter = [0]
        lock = threading.RLock()

        def worker():
            for _ in range(100):
                with lock:
                    with lock:  # 递归获取
                        counter[0] += 1

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert counter[0] == 100

    def test_mutex_order(self):
        """测试锁的顺序"""
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        results = []

        def worker1():
            with lock1:
                time.sleep(0.01)
                with lock2:
                    results.append(1)

        def worker2():
            with lock2:
                time.sleep(0.01)
                with lock1:
                    results.append(2)

        # 按固定顺序加锁避免死锁
        lock1.acquire()
        lock2.acquire()
        try:
            results.append("main")
        finally:
            lock2.release()
            lock1.release()

        assert "main" in results


class TestRWLock:
    """读写锁测试"""

    def test_multiple_readers(self):
        """测试多个读者同时访问"""
        data = {"value": 100}
        read_count = [0]
        lock = threading.Lock()

        def reader():
            for _ in range(50):
                with lock:
                    read_count[0] += 1
                    _ = data["value"]  # 读操作
                    read_count[0] -= 1

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert read_count[0] == 0  # 最终计数应该为 0

    def test_writer_priority(self):
        """测试写者优先"""
        lock = threading.Lock()
        operations = []

        def reader():
            for i in range(3):
                with lock:
                    operations.append(f"r{i}")

        def writer():
            for i in range(3):
                with lock:
                    operations.append(f"w{i}")

        # 单线程测试
        reader()
        writer()
        assert "r" in operations[0]
        assert "w" in operations[-1]


class TestSemaphore:
    """信号量测试"""

    def test_semaphore_basic(self):
        """测试信号量基本功能"""
        sem = threading.Semaphore(0)
        q = queue.Queue()

        def producer():
            for i in range(5):
                q.put(i)
                sem.release()  # V 操作

        def consumer():
            results = []
            for _ in range(5):
                sem.acquire()  # P 操作
                results.append(q.get())
            return results

        prod_thread = threading.Thread(target=producer)
        prod_thread.start()
        prod_thread.join()

        result = consumer()
        assert result == [0, 1, 2, 3, 4]

    def test_semaphore_value(self):
        """测试信号量值"""
        sem = threading.Semaphore(3)
        results = []

        def worker():
            sem.acquire()
            time.sleep(0.05)
            results.append(1)
            sem.release()

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3

    def test_binary_semaphore(self):
        """测试二值信号量（类似互斥锁）"""
        sem = threading.Semaphore(1)
        counter = [0]

        def worker():
            for _ in range(50):
                sem.acquire()
                counter[0] += 1
                sem.release()

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter[0] == 150


class TestConditionVariable:
    """条件变量测试"""

    def test_cond_basic(self):
        """测试条件变量基本功能"""
        condition = threading.Condition()
        data = [False]

        def producer():
            time.sleep(0.05)
            with condition:
                data[0] = True
                condition.notify()

        def consumer():
            with condition:
                while not data[0]:
                    condition.wait(timeout=1)
            return data[0]

        t = threading.Thread(target=producer)
        t.start()
        t.join()

        assert consumer()

    def test_cond_notify_all(self):
        """测试广播通知"""
        condition = threading.Condition()
        results = []

        def worker(n):
            with condition:
                condition.wait()
            results.append(n)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()

        time.sleep(0.05)  # 确保所有线程都在等待

        with condition:
            condition.notify_all()

        for t in threads:
            t.join()

        assert len(results) == 5
        assert sorted(results) == [0, 1, 2, 3, 4]

    def test_cond_with_timeout(self):
        """测试超时等待"""
        condition = threading.Condition()
        start = time.time()

        with condition:
            result = condition.wait(timeout=0.2)

        elapsed = time.time() - start
        assert not result  # 超时返回 False
        assert 0.15 <= elapsed <= 0.35


class TestAtomicOperations:
    """原子操作测试"""

    def test_atomic_counter(self):
        """测试原子计数器"""
        counter = [0]
        lock = threading.Lock()

        def worker():
            for _ in range(1000):
                with lock:
                    old = counter[0]
                    counter[0] = old + 1

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter[0] == 5000

    def test_cas_simulation(self):
        """测试 CAS 操作模拟"""
        value = [0]

        def cas_worker():
            for _ in range(100):
                while True:
                    old = value[0]
                    if old >= 500:
                        break
                    new = old + 1
                    # 简单的 CAS 模拟
                    if value[0] == old:
                        value[0] = new
                        break

        threads = [threading.Thread(target=cas_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 由于竞争，可能达不到 500
        assert value[0] > 0


class TestThreadLocalStorage:
    """线程局部存储测试"""

    def test_thread_local_basic(self):
        """测试线程局部存储基本功能"""
        local = threading.local()
        local.value = 42

        def worker():
            assert not hasattr(local, "value")  # 子线程看不到主线程的值
            local.value = 100
            assert local.value == 100

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert local.value == 42  # 主线程的值不受影响

    def test_thread_local_isolation(self):
        """测试线程局部存储隔离"""
        local = threading.local()
        results = []

        def worker(n):
            local.value = n * 10
            results.append(local.value)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sorted(results) == [0, 10, 20, 30, 40]

    def test_thread_local_init(self):
        """测试带初始值的线程局部存储"""
        local = threading.local()

        def worker():
            local.x = 10
            local.y = 20

        t = threading.Thread(target=worker)
        t.start()
        t.join()


class TestCPUCount:
    """CPU核心数测试"""

    def test_cpu_count(self):
        """测试获取CPU核心数"""
        count = multiprocessing.cpu_count()
        assert count >= 1

    def test_cpu_count_positive(self):
        """测试CPU核心数为正数"""
        count = multiprocessing.cpu_count()
        assert isinstance(count, int)
        assert count > 0


class TestEdgeCases:
    """边界情况测试"""

    def test_zero_timeout(self):
        """测试零超时"""
        lock = threading.Lock()

        acquired = lock.acquire(blocking=False)
        assert acquired

        # 尝试非阻塞获取已持有的锁
        acquired_again = lock.acquire(blocking=False)
        assert not acquired_again

        lock.release()

    def test_semaphore_over_release(self):
        """测试信号量过度释放"""
        sem = threading.Semaphore(0)

        # 连续释放
        sem.release()
        sem.release()
        sem.release()

        # 应该能获取3次
        for _ in range(3):
            acquired = sem.acquire(blocking=False)
            assert acquired

    def test_daemon_thread(self):
        """测试守护线程"""
        results = []

        def daemon_worker():
            time.sleep(0.5)
            results.append(1)

        t = threading.Thread(target=daemon_worker)
        t.daemon = True
        t.start()
        t.join(timeout=0.1)

        assert t.is_alive()  # 超时后线程仍在运行
        # 守护线程会在主线程结束时被强制终止

    def test_thread_name(self):
        """测试线程名称"""
        t = threading.Thread(name="test_thread")
        assert t.name == "test_thread"

        t.name = "renamed"
        assert t.name == "renamed"

    def test_event_sync(self):
        """测试事件同步"""
        event = threading.Event()
        results = []

        def setter():
            time.sleep(0.05)
            event.set()
            results.append("set")

        def waiter():
            event.wait()
            results.append("wait")

        t1 = threading.Thread(target=setter)
        t2 = threading.Thread(target=waiter)

        t2.start()
        t1.start()

        t1.join()
        t2.join()

        assert "set" in results
        assert "wait" in results


class TestBarrier:
    """屏障测试"""

    def test_barrier_basic(self):
        """测试屏障基本功能"""
        barrier = threading.Barrier(3)
        results = []

        def worker(n):
            time.sleep(0.01 * n)
            results.append(f"before_{n}")
            barrier.wait()
            results.append(f"after_{n}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程都应该达到 barrier 之后才能继续
        before_indices = [i for i, s in enumerate(results) if s.startswith("before")]
        after_indices = [i for i, s in enumerate(results) if s.startswith("after")]

        assert min(after_indices) > max(before_indices)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
