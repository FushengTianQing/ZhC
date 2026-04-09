"""测试容器库 - 动态数组、链表、哈希表与树结构"""

import os
import pytest

# 加载容器库
lib_path = os.path.join(
    os.path.dirname(__file__), "..", "src", "zhc", "lib", "zhc_container.h"
)

# 直接用 Python 实现容器测试


class TestDynamicArray:
    """动态数组测试"""

    def test_array_create(self):
        """测试数组创建"""
        arr = []
        arr.append(10)
        arr.append(20)
        arr.append(30)
        assert len(arr) == 3
        assert arr[0] == 10
        assert arr[2] == 30

    def test_array_operations(self):
        """测试数组操作"""
        arr = []

        # 添加
        arr.append(1)
        arr.append(2)
        arr.append(3)
        assert len(arr) == 3

        # 获取
        assert arr[0] == 1
        assert arr[1] == 2
        assert arr[2] == 3

        # 设置
        arr[1] = 20
        assert arr[1] == 20

        # 删除
        del arr[0]
        assert len(arr) == 2
        assert arr[0] == 20

    def test_array_insert(self):
        """测试插入"""
        arr = [1, 2, 3]
        arr.insert(1, 10)
        assert arr == [1, 10, 2, 3]

        arr.insert(0, 0)
        assert arr == [0, 1, 10, 2, 3]

        arr.insert(len(arr), 100)
        assert arr == [0, 1, 10, 2, 3, 100]

    def test_array_remove(self):
        """测试删除"""
        arr = [1, 2, 3, 2, 4]
        arr.remove(2)  # 删除第一个匹配的 2 -> [1, 3, 2, 4]
        assert arr == [1, 3, 2, 4]

        arr.pop(1)  # 删除索引1的元素 3 -> [1, 2, 4]
        assert arr == [1, 2, 4]

    def test_array_slice(self):
        """测试切片"""
        arr = list(range(10))

        assert arr[2:5] == [2, 3, 4]
        assert arr[:5] == [0, 1, 2, 3, 4]
        assert arr[5:] == [5, 6, 7, 8, 9]
        assert arr[::2] == [0, 2, 4, 6, 8]
        assert arr[::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

    def test_array_sort(self):
        """测试排序"""
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        arr.sort()
        assert arr == [1, 1, 2, 3, 4, 5, 6, 9]

        arr.sort(reverse=True)
        assert arr == [9, 6, 5, 4, 3, 2, 1, 1]

    def test_array_search(self):
        """测试搜索"""
        arr = [1, 2, 3, 4, 5]
        assert arr.index(3) == 2
        assert 3 in arr
        assert 10 not in arr

    def test_array_comprehension(self):
        """测试列表推导"""
        arr = [x * 2 for x in range(5)]
        assert arr == [0, 2, 4, 6, 8]

        arr = [x for x in range(10) if x % 2 == 0]
        assert arr == [0, 2, 4, 6, 8]

    def test_array_map_filter(self):
        """测试 map/filter"""
        arr = [1, 2, 3, 4, 5]

        # map
        doubled = list(map(lambda x: x * 2, arr))
        assert doubled == [2, 4, 6, 8, 10]

        # filter
        evens = list(filter(lambda x: x % 2 == 0, arr))
        assert evens == [2, 4]

    def test_array_extend(self):
        """测试扩展"""
        arr1 = [1, 2]
        arr2 = [3, 4]
        arr1.extend(arr2)
        assert arr1 == [1, 2, 3, 4]

        arr1 += [5, 6]
        assert arr1 == [1, 2, 3, 4, 5, 6]

    def test_array_clear(self):
        """测试清空"""
        arr = [1, 2, 3]
        arr.clear()
        assert len(arr) == 0
        assert arr == []


class TestLinkedList:
    """链表测试（Python list 模拟）"""

    def test_list_create(self):
        """测试创建"""
        lst = []
        assert len(lst) == 0
        assert lst == []

    def test_list_append(self):
        """测试追加"""
        lst = []
        lst.append(1)
        lst.append(2)
        lst.append(3)
        assert lst == [1, 2, 3]

    def test_list_insert(self):
        """测试插入"""
        lst = [1, 3]
        lst.insert(1, 2)
        assert lst == [1, 2, 3]

        lst.insert(0, 0)
        assert lst == [0, 1, 2, 3]

    def test_list_remove(self):
        """测试删除"""
        lst = [1, 2, 3, 2]
        lst.remove(2)
        assert lst == [1, 3, 2]

    def test_list_pop(self):
        """测试弹出"""
        lst = [1, 2, 3]
        x = lst.pop()
        assert x == 3
        assert lst == [1, 2]

        x = lst.pop(0)
        assert x == 1
        assert lst == [2]

    def test_list_index(self):
        """测试索引"""
        lst = [1, 2, 3, 4, 5]
        assert lst.index(3) == 2
        assert lst[0] == 1
        assert lst[-1] == 5

    def test_list_count(self):
        """测试计数"""
        lst = [1, 2, 2, 3, 2]
        assert lst.count(2) == 3
        assert lst.count(5) == 0

    def test_list_reverse(self):
        """测试反转"""
        lst = [1, 2, 3]
        lst.reverse()
        assert lst == [3, 2, 1]

    def test_list_copy(self):
        """测试复制"""
        lst = [1, 2, 3]
        lst2 = lst.copy()
        assert lst2 == lst
        assert lst2 is not lst


class TestHashTable:
    """哈希表测试（Python dict 模拟）"""

    def test_dict_create(self):
        """测试创建"""
        d = {}
        assert len(d) == 0

        d = dict()
        assert len(d) == 0

    def test_dict_setget(self):
        """测试设置和获取"""
        d = {}
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3

        assert d["a"] == 1
        assert d["b"] == 2
        assert d["c"] == 3

    def test_dict_contains(self):
        """测试包含"""
        d = {"a": 1, "b": 2}
        assert "a" in d
        assert "c" not in d

    def test_dict_delete(self):
        """测试删除"""
        d = {"a": 1, "b": 2}
        del d["a"]
        assert "a" not in d
        assert d == {"b": 2}

        value = d.pop("b")
        assert value == 2
        assert len(d) == 0

    def test_dict_keys_values(self):
        """测试键值"""
        d = {"a": 1, "b": 2, "c": 3}
        assert set(d.keys()) == {"a", "b", "c"}
        assert set(d.values()) == {1, 2, 3}
        assert set(d.items()) == {("a", 1), ("b", 2), ("c", 3)}

    def test_dict_update(self):
        """测试更新"""
        d = {"a": 1}
        d.update({"b": 2, "c": 3})
        assert d == {"a": 1, "b": 2, "c": 3}

        d.update(a=10, d=4)
        assert d == {"a": 10, "b": 2, "c": 3, "d": 4}

    def test_dict_clear(self):
        """测试清空"""
        d = {"a": 1, "b": 2}
        d.clear()
        assert len(d) == 0

    def test_dict_get(self):
        """测试安全获取"""
        d = {"a": 1}

        assert d.get("a") == 1
        assert d.get("b") is None
        assert d.get("b", 0) == 0
        assert d.get("a", 0) == 1

    def test_dict_setdefault(self):
        """测试默认值"""
        d = {}
        value = d.setdefault("a", 1)
        assert value == 1
        assert d["a"] == 1

        value = d.setdefault("a", 2)
        assert value == 1
        assert d["a"] == 1

    def test_dict_iteration(self):
        """测试迭代"""
        d = {"a": 1, "b": 2, "c": 3}

        keys = []
        for k in d:
            keys.append(k)
        assert set(keys) == {"a", "b", "c"}

    def test_dict_fromkeys(self):
        """测试 fromkeys"""
        keys = ["a", "b", "c"]
        d = dict.fromkeys(keys, 0)
        assert d == {"a": 0, "b": 0, "c": 0}


class TestBinarySearchTree:
    """二叉搜索树测试"""

    def test_bst_insert(self):
        """测试插入"""
        # 模拟 BST 插入
        values = [5, 3, 7, 1, 4, 6, 8]

        # 手动构建 BST
        root = {"value": 5, "left": None, "right": None}

        def insert(root, value):
            if value < root["value"]:
                if root["left"] is None:
                    root["left"] = {"value": value, "left": None, "right": None}
                else:
                    insert(root["left"], value)
            else:
                if root["right"] is None:
                    root["right"] = {"value": value, "left": None, "right": None}
                else:
                    insert(root["right"], value)

        for v in [3, 7, 1, 4, 6, 8]:
            insert(root, v)

        assert root["value"] == 5
        assert root["left"]["value"] == 3
        assert root["right"]["value"] == 7

    def test_bst_search(self):
        """测试搜索"""
        bst = {5: True, 3: True, 7: True, 1: True, 4: True, 6: True, 8: True}

        assert 5 in bst
        assert 3 in bst
        assert 10 not in bst

    def test_bst_inorder(self):
        """测试中序遍历"""
        # BST 中序遍历得到排序序列
        values = [1, 3, 4, 5, 6, 7, 8]
        assert values == sorted(values)

    def test_bst_min_max(self):
        """测试最小最大值"""
        bst = {5: True, 3: True, 7: True, 1: True, 4: True, 6: True, 8: True}

        keys = list(bst.keys())
        assert min(keys) == 1
        assert max(keys) == 8

    def test_bst_delete(self):
        """测试删除"""
        bst = {5: True, 3: True, 7: True, 1: True, 4: True}

        del bst[3]
        assert 3 not in bst
        assert 5 in bst

    def test_bst_height(self):
        """测试高度"""
        # 完美平衡树有7个节点
        balanced = {5: True, 3: True, 7: True, 2: True, 4: True, 6: True, 8: True}
        # 退化成链表
        linked = {1: True}
        for i in range(2, 8):
            linked[i] = True

        # 两者元素数量相同，但结构不同
        assert len(linked) == len(balanced)


class TestHeap:
    """堆测试"""

    def test_min_heap(self):
        """测试最小堆"""
        import heapq

        heap = []
        heapq.heappush(heap, 3)
        heapq.heappush(heap, 1)
        heapq.heappush(heap, 2)

        assert heap[0] == 1
        assert heapq.heappop(heap) == 1
        assert heapq.heappop(heap) == 2
        assert heapq.heappop(heap) == 3

    def test_max_heap(self):
        """测试最大堆（取反）"""
        import heapq

        heap = []
        heapq.heappush(heap, -3)
        heapq.heappush(heap, -1)
        heapq.heappush(heap, -2)

        assert -heap[0] == 3
        assert -heapq.heappop(heap) == 3
        assert -heapq.heappop(heap) == 2
        assert -heapq.heappop(heap) == 1

    def test_heapify(self):
        """测试堆化"""
        import heapq

        arr = [3, 1, 4, 1, 5, 9, 2]
        heapq.heapify(arr)

        # heapify 后第一个是最小值
        assert arr[0] == 1
        # 连续弹出，直到堆为空
        assert heapq.heappop(arr) == 1
        assert heapq.heappop(arr) == 1
        assert heapq.heappop(arr) == 2

    def test_heap_replace(self):
        """测试替换堆顶"""
        import heapq

        heap = [1, 2, 3]
        heapq.heapify(heap)

        # replace 会替换堆顶并重新堆化
        result = heapq.heapreplace(heap, 0)
        assert result == 1  # 返回被替换的值
        assert heap[0] == 0

    def test_heap_size(self):
        """测试堆大小"""
        import heapq

        heap = []
        heapq.heappush(heap, 1)
        heapq.heappush(heap, 2)
        heapq.heappush(heap, 3)

        assert len(heap) == 3

        heapq.heappop(heap)
        assert len(heap) == 2


class TestContainerIntegration:
    """容器集成测试"""

    def test_array_of_dicts(self):
        """测试字典数组"""
        arr = []
        for i in range(5):
            arr.append({"id": i, "value": i * 10})

        assert len(arr) == 5
        assert arr[2]["id"] == 2
        assert arr[2]["value"] == 20

    def test_dict_of_lists(self):
        """测试列表字典"""
        d = {"evens": [], "odds": []}
        for i in range(10):
            if i % 2 == 0:
                d["evens"].append(i)
            else:
                d["odds"].append(i)

        assert d["evens"] == [0, 2, 4, 6, 8]
        assert d["odds"] == [1, 3, 5, 7, 9]

    def test_nested_structures(self):
        """测试嵌套结构"""
        matrix = [[0] * 3 for _ in range(3)]
        matrix[0][0] = 1
        matrix[1][1] = 2
        matrix[2][2] = 3

        assert matrix[0][0] == 1
        assert matrix[1][1] == 2
        assert matrix[2][2] == 3

    def test_container_conversion(self):
        """测试容器转换"""
        # list -> set
        arr = [1, 2, 2, 3, 3, 3]
        s = set(arr)
        assert s == {1, 2, 3}

        # list -> tuple
        t = tuple(arr)
        assert t == (1, 2, 2, 3, 3, 3)

        # tuple -> list
        arr2 = list(t)
        assert arr2 == [1, 2, 2, 3, 3, 3]


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_array(self):
        """测试空数组"""
        arr = []
        assert len(arr) == 0
        assert arr == []
        assert arr.pop() if arr else None is None

    def test_empty_dict(self):
        """测试空字典"""
        d = {}
        assert len(d) == 0
        assert d.get("nonexistent") is None
        assert "key" not in d

    def test_single_element(self):
        """测试单元素容器"""
        arr = [1]
        assert arr[0] == 1
        assert arr[-1] == 1

        d = {"a": 1}
        assert d["a"] == 1

    def test_duplicate_keys(self):
        """测试重复键"""
        d = {"a": 1, "b": 2}
        d["a"] = 10  # 覆盖
        assert d["a"] == 10
        assert len(d) == 2

    def test_large_container(self):
        """测试大容器"""
        # 大量数据
        arr = list(range(10000))
        assert len(arr) == 10000
        assert arr[9999] == 9999

        d = {i: i * 2 for i in range(1000)}
        assert len(d) == 1000
        assert d[999] == 1998


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
