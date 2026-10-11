def build_item_id(task_type: str, index: int) -> str:
    return f"{task_type}_{index:03d}"
