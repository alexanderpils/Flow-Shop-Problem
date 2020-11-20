import numpy as np
from typing import List, Set, Tuple


class Node:
    """[summary]
    """

    def __init__(
        self,
        job_list: List[List[int]],
        nextjob: int,
        number_of_jobs: List[int],
        machine_plan: Tuple[np.ndarray, np.ndarray] = (np.array([]), np.array([])),
        **kwargs
    ):
        self.parent = kwargs.pop("parent", "root")
        self.nextjob = nextjob
        self.order = kwargs.pop("order", []) + [nextjob]
        if kwargs:
            raise TypeError("Unexpected **kwargs: %r" % kwargs)

        self.machine_plan = self.add_job(
            machine_plan[0], machine_plan[1], job_list[nextjob - 1], nextjob
        )
        self.lowerbound(
            self.machine_plan[0],
            self.machine_plan[1],
            self.order,
            job_list,
            number_of_jobs,
        )

    def __le__(self, other):
        return self.lb_value <= other.lb_value

    def __ge__(self, other):
        return self.lb_value >= other.lb_value

    def __lt__(self, other):
        return self.lb_value < other.lb_value

    def __gt__(self, other):
        return self.lb_value > other.lb_value

    def valide_order(self, machine_1, machine_2):
        if len(machine_1) > len(machine_2):
            return False

        return np.all(
            (machine_1 != machine_2[0 : len(machine_1)])
            | ((machine_1 == 0) & (machine_2[0 : len(machine_1)] == 0))
        )
    
    @staticmethod
    def add_job(machine_1, machine_2, job, jobname, gap=False):
        machine_1 = np.append(machine_1, np.repeat(jobname, job[0]))
        if gap:
            gap_size = 0
        else:
            gap_size = max(len(machine_1) - len(machine_2), 0)
        machine_2 = np.concatenate(
            [machine_2, np.repeat(0, gap_size), np.repeat(jobname, job[1])]
        )
        return (machine_1, machine_2)

    def lowerbound(self, machine_1, machine_2, order, job_list, number_of_jobs):
        missing_jobs = [x for x in number_of_jobs if x not in order]
        missing_jobs_plan = [
            x for i, x in enumerate(job_list) if (i + 1) in missing_jobs
        ]
        new_jobs_order = [
            job_id
            for _, job_id in sorted(
                zip([job_plan[1] for job_plan in missing_jobs_plan], missing_jobs)
            )
        ]
        for job_id in new_jobs_order:
            machine_1, machine_2 = self.add_job(
                machine_1, machine_2, job_list[job_id - 1], job_id, gap=True
            )
        self.lb_value = self.calculate_duration(machine_2)
        self.valid = self.valide_order(machine_1, machine_2)
        if self.valid:
            self.order += new_jobs_order
            self.machine_plan = (machine_1, machine_2)

    def calculate_duration(self, machine_2):
        return sum([
            np.max(np.where(machine_2 == x)) for x in set(machine_2[machine_2 != 0])
        ])


class FlowShop:
    def __init__(self, job_list):
        self.job_list = job_list
        self.number_of_jobs = range(1, len(job_list) + 1)
        self.nodes = []
        self.searchnodes = []
        self.create_tree()

    def create_tree(self):
        i = 0
        for job in self.number_of_jobs:
            self.create_node(nextjob=job)
        while self.searchnodes:
            bestnode = min(self.searchnodes)
            for nextjob in [
                possiblejobs
                for possiblejobs in self.number_of_jobs
                if possiblejobs not in bestnode.order
            ]:
                i += 1
                self.create_node(
                    nextjob=nextjob,
                    machine_plan=bestnode.machine_plan,
                    parent=str(bestnode),
                    order=bestnode.order,
                )
            if i > 200000000:
                print("BREAK!!!")
                self.iterations = i
                break
            if bestnode in self.searchnodes:
                self.searchnodes.remove(bestnode)
        self.iterations = i

    def create_node(self, nextjob, **kwargs):
        node = Node(
            job_list=self.job_list,
            nextjob=nextjob,
            number_of_jobs=self.number_of_jobs,
            **kwargs
        )
        self.nodes.append(node)
        if node.valid:
            self.add_solution(node)
        else:
            self.add_searchnode(node)

    def add_solution(self, node):
        if hasattr(self, "solution"):
            if node.lb_value < self.solution.lb_value:
                self.solution = node
        else:
            self.solution = node
        for removenode in [
            searchnode for searchnode in self.searchnodes if node <= searchnode
        ]:
            self.searchnodes.remove(removenode)

    def add_searchnode(self, node):
        if hasattr(self, "solution"):
            if node.lb_value < self.solution.lb_value:
                self.searchnodes.append(node)
        else:
            self.searchnodes.append(node)
