"""Repeatable local demo data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CaseRow, ProjectRow

DEMO_PROJECT_ID = "00000000-0000-0000-0000-000000000001"
DEMO_CASE_ID = "00000000-0000-0000-0000-000000000101"


def seed_demo(session: Session) -> ProjectRow:
    project = session.get(ProjectRow, DEMO_PROJECT_ID)
    if project is None:
        project = ProjectRow(
            id=DEMO_PROJECT_ID,
            name="AgentReliability Demo",
            description="Deterministic local evaluation examples",
        )
        session.add(project)
        session.flush()

    existing_case = session.scalar(
        select(CaseRow).where(
            CaseRow.project_id == DEMO_PROJECT_ID,
            CaseRow.slug == "refund-policy",
        )
    )
    if existing_case is None:
        session.add(
            CaseRow(
                id=DEMO_CASE_ID,
                project_id=DEMO_PROJECT_ID,
                slug="refund-policy",
                name="Refund within 30 days",
                input="How long do I have to request a refund?",
                expectation={
                    "expected_answer": "Refunds are available within 30 days.",
                    "expected_tools": ["lookup_policy"],
                    "prohibited_text": [],
                    "max_latency_ms": 1000.0,
                    "max_total_tokens": 200,
                },
                mock_scenario="pass",
            )
        )
    session.commit()
    session.refresh(project)
    return project
