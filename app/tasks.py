# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from enum import StrEnum


class TaskStatus(StrEnum):
    UNKNOWN = "unknown"
    PENDING = "needsAction"
    COMPLETED = "completed"

    @classmethod
    def _missing_(cls, value: str):
        for member in cls:
            if member.value.casefold() == value.casefold():
                return member
        return None


# https://developers.google.com/tasks/reference/rest/v1/tasks
@dataclass
class Task:
    """Task definition matching Google Task API"""

    id: str
    title: str
    note: str
    position: int
    status: TaskStatus
    subtasks: list[Task]
    due: str = ""

    def __eq__(self, other: Task) -> bool:
        return (
            self.title == other.title
            and self.note == other.note
            and self.status == other.status
            and self.subtasks == other.subtasks
        )

    def __str__(self) -> str:
        return (
            f"#{self.position}: {self.title} ({self.id}): "
            f"{self.status}, {len(self.subtasks)} subtasks"
        )

    def completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def to_request(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": "tasks#task",
            "notes": self.note,
            "status": self.status.value,
            "title": self.title,
        }


# https://developers.google.com/tasks/reference/rest/v1/tasklists
@dataclass
class TaskList:
    """Tasklist definition matching Google Task API"""

    id: str
    title: str
    tasks: list[Task]

    def __eq__(self, other: TaskList) -> bool:
        return self.title == other.title and self.tasks == other.tasks

    def __str__(self) -> str:
        return f"{self.title} ({self.id}): {len(self.tasks)} tasks"

    def to_request(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": "tasks#taskList",
            "title": self.title,
        }


def filter_task_lists_due_soon(
    task_lists: list[TaskList], days: int = 7, today: date | None = None
) -> list[TaskList]:
    """
    Keeps only overdue, incomplete tasks and incomplete tasks due within the
    next `days` days.

    Completed tasks are never kept, since there's nothing left to pay
    attention to. A task with no due date of its own is kept if it has a
    subtask that matches, so the parent remains for context; task lists left
    with no tasks after filtering are dropped.
    """
    cutoff = (today or date.today()) + timedelta(days=days)

    def task_matches(task: Task) -> bool:
        if task.completed():
            return False
        if not task.due:
            return False
        return date.fromisoformat(task.due.split("T")[0]) <= cutoff

    def filter_tasks(tasks: list[Task]) -> list[Task]:
        filtered = []
        for task in tasks:
            subtasks = filter_tasks(task.subtasks)
            if task_matches(task) or subtasks:
                filtered.append(replace(task, subtasks=subtasks))
        return filtered

    filtered_task_lists = []
    for task_list in task_lists:
        tasks = filter_tasks(task_list.tasks)
        if tasks:
            filtered_task_lists.append(replace(task_list, tasks=tasks))
    return filtered_task_lists
