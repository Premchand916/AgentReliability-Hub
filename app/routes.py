"""Thin HTTP routes for projects and evaluation cases."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CaseRow, ProjectRow
from app.schemas import CaseCreate, CaseList, Project, ProjectCreate, ProjectList, TestCase

router = APIRouter(prefix="/api")


def get_session(request: Request):
    yield from request.app.state.database.sessions()


def project_from_row(row: ProjectRow) -> Project:
    return Project.model_validate(row, from_attributes=True)


def case_from_row(row: CaseRow) -> TestCase:
    return TestCase.model_validate(row, from_attributes=True)


def project_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "project_not_found", "message": "Project not found"}},
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    row = ProjectRow(
        id=str(uuid4()),
        **payload.model_dump(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return project_from_row(row)


@router.get("/projects", response_model=ProjectList)
def list_projects(session: Session = Depends(get_session)) -> ProjectList:
    rows = session.scalars(select(ProjectRow).order_by(ProjectRow.created_at, ProjectRow.id))
    return ProjectList(items=[project_from_row(row) for row in rows])


@router.get("/projects/{project_id}", response_model=Project)
def read_project(project_id: str, session: Session = Depends(get_session)) -> Project:
    row = session.get(ProjectRow, project_id)
    if row is None:
        raise project_not_found()
    return project_from_row(row)


@router.post(
    "/projects/{project_id}/cases",
    response_model=TestCase,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    project_id: str,
    payload: CaseCreate,
    session: Session = Depends(get_session),
) -> TestCase:
    if session.get(ProjectRow, project_id) is None:
        raise project_not_found()
    row = CaseRow(
        id=str(uuid4()),
        project_id=project_id,
        **payload.model_dump(mode="json"),
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "duplicate_case_slug", "message": "Case slug already exists"}},
        ) from None
    session.refresh(row)
    return case_from_row(row)


@router.get("/projects/{project_id}/cases", response_model=CaseList)
def list_cases(project_id: str, session: Session = Depends(get_session)) -> CaseList:
    if session.get(ProjectRow, project_id) is None:
        raise project_not_found()
    rows = session.scalars(
        select(CaseRow)
        .where(CaseRow.project_id == project_id)
        .order_by(CaseRow.created_at, CaseRow.id)
    )
    return CaseList(items=[case_from_row(row) for row in rows])
