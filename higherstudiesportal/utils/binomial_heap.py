from datetime import datetime
from typing import List

class BinomialNode:
    def __init__(self, student, priority):
        self.student = student  # dict with name, regno, admission_date, etc.
        self.priority = priority  # number of days left (lower = higher priority)
        self.children = []
        self.degree = 0


class BinomialHeap:
    def __init__(self):
        self.trees = []

    def merge_trees(self, t1, t2):
        if t1.priority > t2.priority:
            t1, t2 = t2, t1
        t1.children.append(t2)
        t1.degree += 1
        return t1

    def insert(self, student, priority):
        new_heap = BinomialHeap()
        new_heap.trees.append(BinomialNode(student, priority))
        self.union(new_heap)

    def union(self, other):
        new_trees = []
        i = j = 0
        carry = None

        while i < len(self.trees) or j < len(other.trees) or carry:
            t1 = self.trees[i] if i < len(self.trees) else None
            t2 = other.trees[j] if j < len(other.trees) else None

            degrees = {t.degree for t in [t1, t2, carry] if t}
            if not degrees:
                break
            degree = min(degrees)
            same_degree = [t for t in [t1, t2, carry] if t and t.degree == degree]

            if len(same_degree) == 1:
                new_trees.append(same_degree[0])
                if same_degree[0] == t1: i += 1
                elif same_degree[0] == t2: j += 1
                else: carry = None
            elif len(same_degree) == 2:
                carry = self.merge_trees(same_degree[0], same_degree[1])
                if t1 in same_degree: i += 1
                if t2 in same_degree: j += 1
            else:  # len == 3
                new_trees.append(same_degree[0])
                carry = self.merge_trees(same_degree[1], same_degree[2])
                i += 1
                j += 1

        self.trees = new_trees

    def extract_min(self):
        if not self.trees:
            return None

        min_index = min(range(len(self.trees)), key=lambda i: self.trees[i].priority)
        min_node = self.trees.pop(min_index)

        child_heap = BinomialHeap()
        child_heap.trees = list(reversed(min_node.children))
        self.union(child_heap)

        return min_node.student

    def is_empty(self):
        return len(self.trees) == 0

    def get_sorted_requests(self) -> List[dict]:
        results = []
        while not self.is_empty():
            results.append(self.extract_min())
        return results
