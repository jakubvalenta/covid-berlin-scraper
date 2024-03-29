import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

import regex
from sqlalchemy import (
    DateTime, Integer, LargeBinary, String, create_engine, select,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, mapped_column, scoped_session,
    sessionmaker,
)

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class PressRelease(Base):  # type: ignore
    __tablename__ = 'press_releases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    def matches_title_regex(self, title_regex: regex.Pattern) -> bool:
        return bool(title_regex.search(self.title))

    def __repr__(self) -> str:
        return (
            f'PressRelease(timestamp={self.timestamp.isoformat()}, '
            f'title={self.title}, '
            f'url={self.url})'
        )


def create_session(path: Path) -> scoped_session[Session]:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{path}', future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


class PressReleasesStore:
    _session: scoped_session[Session]

    def __init__(self, path: Path):
        self._session = create_session(path)

    def list(self) -> Iterator[PressRelease]:
        return self._session.scalars(
            select(PressRelease).order_by(PressRelease.timestamp)
        )

    def append(self, press_release: PressRelease):
        existing_press_release = self._session.scalars(
            select(PressRelease).where(
                PressRelease.timestamp == press_release.timestamp
            )
        ).first()
        if existing_press_release:
            logger.info('Updating existing press release %s', press_release)
            existing_press_release.title = press_release.title
            existing_press_release.url = press_release.url
        else:
            logger.info('Adding new press release %s', press_release)
            self._session.add(press_release)
        self._session.commit()


class DistrictTable(Base):  # type: ignore
    __tablename__ = 'district_table'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, unique=True
    )
    content: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f'DistrictTable(timestamp={self.timestamp.isoformat()}, '
            f'content={self.content})'
        )


class DistrictTableStore:
    _session: scoped_session[Session]

    def __init__(self, path: Path):
        self._session = create_session(path)

    def list(self) -> Iterator[DistrictTable]:
        return self._session.scalars(
            select(DistrictTable).order_by(DistrictTable.timestamp)
        )

    def append(self, district_table: DistrictTable):
        existing_district_table = self._session.scalars(
            select(DistrictTable).where(
                DistrictTable.timestamp == district_table.timestamp
            )
        ).first()
        if existing_district_table:
            logger.info('Updating existing district table %s', district_table)
            district_table.content = district_table.content
        else:
            logger.info('Adding new district table %s', district_table)
            self._session.add(district_table)
        self._session.commit()


class UncompressedDashboard(Base):  # type: ignore
    __tablename__ = 'dashboard'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, unique=True
    )
    content: Mapped[str] = mapped_column(String, nullable=False)

    @property
    def content_utf8(self) -> str:
        try:
            return self.content.encode('iso-8859-1').decode()
        except (UnicodeDecodeError, UnicodeEncodeError):
            return self.content

    def __repr__(self) -> str:
        return (
            f'UncompressedDashboard(timestamp={self.timestamp.isoformat()}, '
            f'content_length={len(self.content)})'
        )


class UncompressedDashboardStore:
    _session: scoped_session[Session]

    def __init__(self, path: Path):
        self._session = create_session(path)

    def list_ids(self, buffer_size: int = 50) -> Iterator[int]:
        return self._session.scalars(
            select(UncompressedDashboard.id).order_by(
                UncompressedDashboard.timestamp
            )
        )

    def find_one(self, id: int) -> UncompressedDashboard | None:
        return self._session.scalar(
            select(UncompressedDashboard).where(UncompressedDashboard.id == id)
        )


class Dashboard(Base):  # type: ignore
    __tablename__ = 'compressed_dashboard'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, unique=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    @property
    def decompressed_content(self) -> bytes:
        return gzip.decompress(self.content)

    @classmethod
    def from_uncompressed_dashboard(
        cls, uncompressed_dashboard: UncompressedDashboard
    ) -> 'Dashboard':
        return cls(
            timestamp=uncompressed_dashboard.timestamp,
            content=gzip.compress(
                uncompressed_dashboard.content_utf8.encode()
            ),
        )

    def __repr__(self) -> str:
        return (
            f'Dashboard(timestamp={self.timestamp.isoformat()}, '
            f'content_length={len(self.content)})'
        )


class DashboardStore:
    _session: scoped_session[Session]

    def __init__(self, path: Path):
        self._session = create_session(path)

    def list(self, buffer_size: int = 50) -> Iterator[Dashboard]:
        result = self._session.execute(
            select(Dashboard)
            .order_by(Dashboard.timestamp)
            .execution_options(
                stream_results=True, max_row_buffer=buffer_size
            ),
        )
        return result.yield_per(buffer_size).scalars()

    def append(self, dashboard: Dashboard):
        existing_dashboard = self._session.scalars(
            select(Dashboard).where(Dashboard.timestamp == dashboard.timestamp)
        ).first()
        if existing_dashboard:
            logger.info(
                'Updating existing dashboard %s',
                dashboard,
            )
            existing_dashboard.content = dashboard.content
        else:
            logger.info('Adding new dashboard %s', dashboard)
            self._session.add(dashboard)
        self._session.commit()
