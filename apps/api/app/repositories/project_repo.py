"""
Project repository — all database access for the Project model.
Business logic lives in project_service.py.
"""
from datetime import UTC

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.trace import Trace
from app.models.user import User


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def lock_owner(self, owner_id: str) -> None:
        # Serialize project-name writes for this account until the request commits.
        # This also protects an empty workspace from concurrent duplicate creates.
        await self.db.execute(select(User.id).where(User.id == owner_id).with_for_update())

    async def name_exists(self, owner_id: str, name: str, exclude_id: str | None = None) -> bool:
        normalized = func.lower(func.btrim(func.regexp_replace(Project.name, r"\s+", " ", "g")))
        query = select(Project.id).where(Project.owner_id == owner_id, normalized == func.lower(name))
        if exclude_id:
            query = query.where(Project.id != exclude_id)
        return (await self.db.execute(query.limit(1))).scalar_one_or_none() is not None

    async def list_with_activity(self, owner_id: str) -> list[dict]:
        from app.schemas.project import ProjectResponse
        rows = (await self.db.execute(select(
            Project,
            func.count(Trace.id).label("trace_count"),
            func.count(Trace.id).filter(Trace.status == "error").label("error_count"),
            func.coalesce(func.sum(cast(Trace.metrics["total_tokens"].astext, Integer)), 0).label("total_tokens"),
            func.coalesce(func.avg(Trace.duration_ms), 0).label("avg_latency_ms"),
            func.max(Trace.started_at).label("last_trace_at"),
        ).outerjoin(Trace, Trace.project_id == Project.id).where(
            Project.owner_id == owner_id, Project.is_active.is_(True)
        ).group_by(Project.id).order_by(Project.created_at.desc()))).all()
        return [{**ProjectResponse.model_validate(row.Project).model_dump(),
                 "trace_count": row.trace_count, "error_count": row.error_count,
                 "total_tokens": row.total_tokens, "avg_latency_ms": float(row.avg_latency_ms),
                 "last_trace_at": row.last_trace_at} for row in rows]

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, owner_id: str, slug: str) -> Project | None:
        result = await self.db.execute(
            select(Project).where(
                Project.owner_id == owner_id,
                Project.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: str) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id, Project.is_active == True)  # noqa: E712
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def count_traces(self, project_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(Trace.project_id == project_id)
        )
        return result.scalar_one() or 0

    async def get_trace_stats(self, project_id: str) -> dict:
        """Return aggregate stats for the overview page."""
        from sqlalchemy import Integer, case, cast

        result = await self.db.execute(
            select(
                func.count(Trace.id).label("total"),
                func.avg(Trace.duration_ms).label("avg_duration_ms"),
                func.sum(
                    cast(case((Trace.status == "error", 1), else_=0), Integer)
                ).label("error_count"),
            ).where(Trace.project_id == project_id)
        )
        row = result.one()
        total = row.total or 0
        avg_duration = float(row.avg_duration_ms or 0)
        error_count = int(row.error_count or 0)

        # Average total_tokens from the metrics JSONB column
        token_result = await self.db.execute(
            select(
                func.avg(
                    func.cast(
                        Trace.metrics["total_tokens"].astext,
                        Integer,
                    )
                ).label("avg_tokens")
            ).where(
                Trace.project_id == project_id,
                Trace.metrics["total_tokens"].astext.isnot(None),
            )
        )
        avg_tokens = float(token_result.scalar_one() or 0)

        from datetime import datetime, timedelta
        cutoff = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29)
        token_value = func.coalesce(cast(Trace.metrics["total_tokens"].astext, Integer), 0)
        totals = (await self.db.execute(select(
            func.sum(token_value), func.count().filter(Trace.status == "success")
        ).where(Trace.project_id == project_id))).one()
        day = func.date_trunc("day", Trace.started_at, "UTC")
        daily_rows = (await self.db.execute(select(day.label("day"), func.count().label("requests"),
            func.sum(token_value).label("tokens")).where(Trace.project_id == project_id,
            Trace.started_at >= cutoff).group_by(day).order_by(day))).all()
        daily = {row.day.date().isoformat(): row for row in daily_rows}
        activity = []
        for offset in range(30):
            label = (cutoff + timedelta(days=offset)).date().isoformat()
            item = daily.get(label)
            activity.append({"date": label, "requests": item.requests if item else 0, "tokens": int(item.tokens or 0) if item else 0})
        bucket = case((Trace.duration_ms < 100, "<100ms"), (Trace.duration_ms < 500, "100–499ms"),
                      (Trace.duration_ms < 1000, "500–999ms"), (Trace.duration_ms < 5000, "1–5s"), else_="≥5s")
        histogram = dict((await self.db.execute(select(bucket, func.count()).where(
            Trace.project_id == project_id).group_by(bucket))).all())

        return {
            "total_tokens": int(totals[0] or 0),
            "success_rate": totals[1] / total if total else 0,
            "activity": activity,
            "latency_buckets": [{"label": label, "count": histogram.get(label, 0)} for label in ["<100ms", "100–499ms", "500–999ms", "1–5s", "≥5s"]],
            "total_traces": total,
            "avg_latency_ms": avg_duration,
            "error_rate": (error_count / total) if total > 0 else 0.0,
            "avg_tokens": avg_tokens,
        }
