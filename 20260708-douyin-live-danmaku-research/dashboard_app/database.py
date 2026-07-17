from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "MySQLConfig":
        return cls(
            host=os.getenv("DANMAKU_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DANMAKU_DB_PORT", "3306")),
            user=os.getenv("DANMAKU_DB_USER", "root"),
            password=os.getenv("DANMAKU_DB_PASSWORD", ""),
            database=os.getenv("DANMAKU_DB_NAME", "douyin_danmaku"),
        )


class DashboardDatabase:
    def __init__(self, config: MySQLConfig | None = None) -> None:
        self.config = config or MySQLConfig.from_env()

    def initialize(self) -> None:
        with self._connect_without_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.config.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )

        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        room_id VARCHAR(128) NOT NULL,
                        source_url TEXT NULL,
                        status VARCHAR(32) NOT NULL,
                        started_at DATETIME(6) NOT NULL,
                        ended_at DATETIME(6) NULL,
                        error_message TEXT NULL,
                        INDEX idx_sessions_started_at (started_at),
                        INDEX idx_sessions_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id BIGINT NOT NULL,
                        room_id VARCHAR(128) NULL,
                        user_id VARCHAR(128) NULL,
                        nickname VARCHAR(255) NULL,
                        content TEXT NOT NULL,
                        event_time DATETIME(6) NULL,
                        received_at DATETIME(6) NOT NULL,
                        method VARCHAR(128) NULL,
                        INDEX idx_chat_session_id_id (session_id, id),
                        INDEX idx_chat_received_at (received_at),
                        INDEX idx_chat_user_id (user_id),
                        CONSTRAINT fk_chat_session FOREIGN KEY (session_id)
                            REFERENCES sessions(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS keyword_hits (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id BIGINT NOT NULL,
                        keyword VARCHAR(64) NOT NULL,
                        hit_count INT NOT NULL DEFAULT 0,
                        last_hit_at DATETIME(6) NOT NULL,
                        UNIQUE KEY uniq_session_keyword (session_id, keyword),
                        INDEX idx_keyword_session_count (session_id, hit_count),
                        CONSTRAINT fk_keyword_session FOREIGN KEY (session_id)
                            REFERENCES sessions(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )

    def connect(self):
        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )

    def create_session(self, room_id: str, source_url: str | None) -> int:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sessions (room_id, source_url, status, started_at)
                    VALUES (%s, %s, 'running', %s)
                    """,
                    (room_id, source_url, datetime.now()),
                )
                return int(cursor.lastrowid)

    def finish_session(self, session_id: int, status: str, error_message: str | None = None) -> None:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE sessions
                    SET status = %s, ended_at = %s, error_message = %s
                    WHERE id = %s
                    """,
                    (status, datetime.now(), error_message, session_id),
                )

    def insert_chat(self, session_id: int, event: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now()
        event_time = parse_event_time(event.get("timestamp"))
        nickname = repair_mojibake(event.get("nickname"))
        content = repair_mojibake(event.get("content")) or ""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages
                    (session_id, room_id, user_id, nickname, content, event_time, received_at, method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        event.get("room_id"),
                        event.get("user_id"),
                        nickname,
                        content,
                        event_time,
                        now,
                        event.get("method"),
                    ),
                )
                message_id = int(cursor.lastrowid)

        self.record_keywords(session_id, content, now)
        return {
            "id": message_id,
            "session_id": session_id,
            "room_id": event.get("room_id"),
            "user_id": event.get("user_id"),
            "nickname": nickname,
            "content": content,
            "event_time": iso_or_none(event_time),
            "received_at": now.isoformat(timespec="seconds"),
            "method": event.get("method"),
        }

    def record_keywords(self, session_id: int, content: str, when: datetime) -> None:
        keywords = extract_keywords(content)
        if not keywords:
            return

        with self.connect() as conn:
            with conn.cursor() as cursor:
                for keyword, count in Counter(keywords).items():
                    cursor.execute(
                        """
                        INSERT INTO keyword_hits (session_id, keyword, hit_count, last_hit_at)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            hit_count = hit_count + VALUES(hit_count),
                            last_hit_at = VALUES(last_hit_at)
                        """,
                        (session_id, keyword, count, when),
                    )

    def latest_messages(self, session_id: int | None, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        where = "WHERE session_id = %s" if session_id else ""
        params: tuple[Any, ...] = (session_id, limit) if session_id else (limit,)
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, session_id, room_id, user_id, nickname, content,
                           event_time, received_at, method
                    FROM chat_messages
                    {where}
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [serialize_message(row) for row in reversed(rows)]

    def user_ranking(self, session_id: int | None, limit: int = 10) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 50))
        where = "WHERE session_id = %s" if session_id else ""
        params: tuple[Any, ...] = (session_id, limit) if session_id else (limit,)
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT COALESCE(NULLIF(nickname, ''), MAX(user_id), '匿名用户') AS nickname,
                           COALESCE(MAX(user_id), '') AS user_id,
                           COUNT(*) AS count
                    FROM chat_messages
                    {where}
                    GROUP BY COALESCE(user_id, nickname, 'anonymous'), nickname
                    ORDER BY count DESC
                    LIMIT %s
                    """,
                    params,
                )
                rows = cursor.fetchall()
        return [
            {
                "nickname": repair_mojibake(row["nickname"]),
                "user_id": row["user_id"],
                "count": int(row["count"]),
            }
            for row in rows
        ]

    def keyword_ranking(self, session_id: int | None, limit: int = 20) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        where = "WHERE session_id = %s" if session_id else ""
        params: tuple[Any, ...] = (session_id, limit) if session_id else (limit,)
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT keyword, hit_count, last_hit_at
                    FROM keyword_hits
                    {where}
                    ORDER BY hit_count DESC, last_hit_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                rows = cursor.fetchall()
        merged: dict[str, dict[str, Any]] = {}
        for row in rows:
            keyword = repair_mojibake(row["keyword"]) or row["keyword"]
            current = merged.setdefault(
                keyword,
                {"keyword": keyword, "hit_count": 0, "last_hit_at": row["last_hit_at"]},
            )
            current["hit_count"] += int(row["hit_count"])
            if row["last_hit_at"] > current["last_hit_at"]:
                current["last_hit_at"] = row["last_hit_at"]
        return [
            {
                "keyword": item["keyword"],
                "hit_count": item["hit_count"],
                "last_hit_at": item["last_hit_at"].isoformat(timespec="seconds"),
            }
            for item in sorted(merged.values(), key=lambda value: value["hit_count"], reverse=True)[:limit]
        ]

    def stats(self, session_id: int | None) -> dict[str, Any]:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        with self.connect() as conn:
            with conn.cursor() as cursor:
                session_filter = "session_id = %s" if session_id else "1=1"
                session_params: tuple[Any, ...] = (session_id,) if session_id else ()

                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM chat_messages WHERE {session_filter}",
                    session_params,
                )
                total = int(cursor.fetchone()["total"])

                cursor.execute(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM chat_messages
                    WHERE {session_filter} AND received_at >= %s
                    """,
                    (*session_params, minute_ago),
                )
                last_minute = int(cursor.fetchone()["total"])

                cursor.execute(
                    f"""
                    SELECT COUNT(DISTINCT COALESCE(user_id, nickname)) AS total
                    FROM chat_messages
                    WHERE {session_filter}
                    """,
                    session_params,
                )
                active_users = int(cursor.fetchone()["total"])

                cursor.execute(
                    f"""
                    SELECT DATE_FORMAT(received_at, '%%H:%%i') AS label,
                           COUNT(*) AS count
                    FROM chat_messages
                    WHERE {session_filter} AND received_at >= %s
                    GROUP BY
                        DATE_FORMAT(received_at, '%%Y-%%m-%%d %%H:%%i'),
                        DATE_FORMAT(received_at, '%%H:%%i')
                    ORDER BY MIN(received_at)
                    """,
                    (*session_params, now - timedelta(minutes=30)),
                )
                trend = [{"label": row["label"], "count": int(row["count"])} for row in cursor.fetchall()]

        return {
            "total_messages": total,
            "last_minute_messages": last_minute,
            "active_users": active_users,
            "keyword_hits": sum(row["hit_count"] for row in self.keyword_ranking(session_id, 20)),
            "trend": trend,
            "keywords": self.keyword_ranking(session_id, 12),
        }

    def export_messages(self, session_id: int | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                if session_id:
                    cursor.execute(
                        """
                        SELECT room_id, user_id, nickname, content, event_time, received_at, method
                        FROM chat_messages
                        WHERE session_id = %s
                        ORDER BY id ASC
                        """,
                        (session_id,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT room_id, user_id, nickname, content, event_time, received_at, method
                        FROM chat_messages
                        ORDER BY id ASC
                        """
                    )
                return list(cursor.fetchall())

    def _connect_without_db(self):
        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )


def parse_event_time(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    if number > 10_000_000_000:
        number = number // 1000
    try:
        return datetime.fromtimestamp(number)
    except (OSError, ValueError):
        return None


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat(timespec="seconds") if value else None


def serialize_message(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "room_id": row["room_id"],
        "user_id": row["user_id"],
        "nickname": repair_mojibake(row["nickname"]),
        "content": repair_mojibake(row["content"]) or "",
        "event_time": iso_or_none(row["event_time"]),
        "received_at": iso_or_none(row["received_at"]),
        "method": row["method"],
    }


STOPWORDS = {
    "一个",
    "这个",
    "那个",
    "什么",
    "怎么",
    "不是",
    "可以",
    "没有",
    "就是",
    "今天",
    "直播",
    "主播",
}


def extract_keywords(content: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z0-9_]{3,20}", content)
    return [token.lower() for token in tokens if token not in STOPWORDS]


def repair_mojibake(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    markers = ("æ", "è", "å", "ç", "é", "ã", "ï¼", "Â", "�")
    if not any(marker in text for marker in markers):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    if cjk_count(repaired) >= cjk_count(text):
        return repaired
    return text


def cjk_count(value: str) -> int:
    return sum(1 for char in value if "\u4e00" <= char <= "\u9fff")
