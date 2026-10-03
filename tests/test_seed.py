from pathlib import Path

from sqlalchemy import func, select

from app.database import Database
from app.models import CaseRow, ProjectRow
from app.seed import DEMO_PROJECT_ID, seed_demo


def test_seed_is_idempotent_and_preserves_user_data(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'seed.db'}")
    database.create_schema()
    with database.session_factory() as session:
        session.add(ProjectRow(id="user-project", name="User Project", description=""))
        session.commit()
        seed_demo(session)
        seed_demo(session)

        assert session.scalar(select(func.count(ProjectRow.id))) == 2
        assert session.scalar(
            select(func.count(CaseRow.id)).where(CaseRow.project_id == DEMO_PROJECT_ID)
        ) == 1
        assert session.get(ProjectRow, "user-project") is not None
    database.dispose()
