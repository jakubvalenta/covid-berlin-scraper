import logging
from pathlib import Path

import regex
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class PressRelease(Base):  # type: ignore
    __tablename__ = 'press_releases'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, unique=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)

    def matches_title_regex(self, title_regex: regex.Regex) -> bool:
        return bool(title_regex.search(self.title))

    def __repr__(self) -> str:
        return (
            f'PressRelease(timestamp={self.timestamp.isoformat()}, '
            f'title={self.title}, '
            f'url={self.url})'
        )


def create_session(path: Path) -> Session:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


class PressReleasesStore(list):
    _session: Session

    def __init__(self, path: Path):
        self._session = create_session(path)
        query = self._session.query(PressRelease).order_by(
            PressRelease.timestamp
        )
        for press_release in query:
            super().append(press_release)

    def append(self, press_release: PressRelease):
        existing_press_release = (
            self._session.query(PressRelease)
            .filter(PressRelease.timestamp == press_release.timestamp)
            .first()
        )
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

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, unique=True)
    content = Column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f'DistrictTable(timestamp={self.timestamp.isoformat()}, '
            f'content={self.content})'
        )


class DistrictTableStore(list):
    _session: Session

    def __init__(self, path: Path):
        self._session = create_session(path)
        query = self._session.query(DistrictTable).order_by(
            DistrictTable.timestamp
        )
        for district_table in query:
            super().append(district_table)

    def append(self, district_table: DistrictTable):
        existing_district_table = (
            self._session.query(DistrictTable)
            .filter(DistrictTable.timestamp == district_table.timestamp)
            .first()
        )
        if existing_district_table:
            logger.info('Updating existing district table %s', district_table)
            district_table.content = district_table.content
        else:
            logger.info('Adding new district table %s', district_table)
            self._session.add(district_table)
        self._session.commit()


class Dashboard(Base):  # type: ignore
    __tablename__ = 'dashboard'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, unique=True)
    content = Column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f'Dashboard(timestamp={self.timestamp.isoformat()}, '
            f'content_length={len(self.content)})'
        )

    @property
    def content_utf8(self) -> str:
        try:
            return self.content.encode('iso-8859-1').decode()
        except (UnicodeDecodeError, UnicodeEncodeError):
            return self.content


class DashboardStore(list):
    _session: Session

    def __init__(self, path: Path):
        self._session = create_session(path)
        query = self._session.query(Dashboard).order_by(Dashboard.timestamp)
        for dashboard in query:
            super().append(dashboard)

    def append(self, dashboard: Dashboard):
        existing_dashboard = (
            self._session.query(Dashboard)
            .filter(Dashboard.timestamp == dashboard.timestamp)
            .first()
        )
        if existing_dashboard:
            logger.info('Updating existing dashboard %s', dashboard)
            dashboard.content = dashboard.content
        else:
            logger.info('Adding new dashboard %s', dashboard)
            self._session.add(dashboard)
        self._session.commit()
