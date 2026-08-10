"""CP1 — Structured logging.

`print("client abc hỏi gì đó")` là log cho người đọc. Cloud (Railway, Render,
Cloud Run, Datadog...) đọc log bằng máy: một dòng = một JSON object thì mới
lọc/đếm/cảnh báo được. Đây là khác biệt lớn giữa localhost và production.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """CHO SẴN — thời điểm hiện tại theo ISO-8601, múi giờ UTC."""
    return datetime.now(timezone.utc).isoformat()


def emit(event: str, severity: str = "INFO", **fields) -> str:
    """Ghi một dòng log JSON ra stdout.

    TODO (CP1): tạo dict gồm tối thiểu 3 khóa
        - "event"    : tên sự kiện, lấy từ tham số ``event``
        - "severity" : mức log, VIẾT HOA (dùng ``severity.upper()``) — đây là
                       tên khóa mà Google Cloud Logging hiểu để tô màu và lọc
        - "ts"       : ``utc_now_iso()``
    rồi gộp thêm mọi cặp key/value trong ``**fields``.

    In chuỗi JSON đó ra stdout **trên một dòng duy nhất**
    (``json.dumps(..., ensure_ascii=False)``, đừng dùng ``indent``) và
    trả về chính chuỗi đó.

    Ví dụ:
        >>> emit("chat_completed", client_id="sv01", usd_cost=0.0001)
        '{"event": "chat_completed", "severity": "INFO", "ts": "...", ...}'
    """

    #{"timestamp": "2026-08-09T10:30:00Z", "level": "INFO", "event": "ask_completed", "user_id": "sv01", "latency_ms": 142}
    log_entry = {
        "event": event,
        "ts": utc_now_iso(),
        "severity": severity.upper(),
        **fields,
    }

    log_line = json.dumps(log_entry, ensure_ascii=False)
    print(log_line)
    return log_line
    #raise NotImplementedError("TODO (CP1): cài đặt emit")
