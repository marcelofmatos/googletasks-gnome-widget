"""fetch_all_tasks: filtragem, ordenação e agrupamento por lista."""
from unittest.mock import MagicMock

from main import fetch_all_tasks


def _service(tasklists, tasks_by_list):
    """Constrói um mock do serviço tasks() respeitando o encadeamento usado no código."""
    service = MagicMock()
    service.tasklists.return_value.list.return_value.execute.return_value = {
        "items": tasklists
    }

    def list_tasks(tasklist, **_):
        call = MagicMock()
        call.execute.return_value = {"items": tasks_by_list.get(tasklist, [])}
        return call

    service.tasks.return_value.list.side_effect = list_tasks
    return service


def test_filters_only_needs_action_tasks():
    svc = _service(
        tasklists=[{"id": "L1", "title": "Work"}],
        tasks_by_list={
            "L1": [
                {"id": "t1", "status": "needsAction", "title": "Pendente"},
                {"id": "t2", "status": "completed",   "title": "Concluída"},
            ],
        },
    )
    result = fetch_all_tasks(svc)
    assert len(result) == 1
    assert [t["id"] for t in result[0]["tasks"]] == ["t1"]


def test_skips_lists_without_pending_tasks():
    svc = _service(
        tasklists=[
            {"id": "L1", "title": "Work"},
            {"id": "L2", "title": "Home"},
        ],
        tasks_by_list={
            "L1": [{"id": "t1", "status": "needsAction"}],
            "L2": [{"id": "t2", "status": "completed"}],
        },
    )
    result = fetch_all_tasks(svc)
    assert [r["list"]["id"] for r in result] == ["L1"]


def test_tasks_with_due_come_before_undated():
    svc = _service(
        tasklists=[{"id": "L1", "title": "Work"}],
        tasks_by_list={
            "L1": [
                {"id": "sem_data", "status": "needsAction"},
                {"id": "dez",      "status": "needsAction", "due": "2025-12-31T00:00:00.000Z"},
                {"id": "jun",      "status": "needsAction", "due": "2025-06-15T00:00:00.000Z"},
            ],
        },
    )
    result = fetch_all_tasks(svc)
    assert [t["id"] for t in result[0]["tasks"]] == ["jun", "dez", "sem_data"]


def test_empty_result_when_no_lists():
    svc = _service(tasklists=[], tasks_by_list={})
    assert fetch_all_tasks(svc) == []
