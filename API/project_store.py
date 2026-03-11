"""
ProjectStore — Persistence layer for EVOLV project / release
hierarchy.

Stores projects, versioned releases, GAMP 5 folder structure,
and a Global Library of reusable System Descriptions and Risk
Matrices.  All data is persisted to
``output/project_store.json`` using a thread-safe singleton.

:requirement: URS-30.1 - System shall organise validation
              artefacts in a hierarchical project/release
              structure.
:requirement: URS-30.2 - System shall auto-populate GAMP 5
              sub-folders when a release is created.
:requirement: URS-30.3 - System shall support moving items
              between releases with full audit logging.
"""
from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

_STORE_PATH = Path("output") / "project_store.json"

# GAMP 5 standard folder template applied to every new release.
GAMP5_FOLDERS: List[str] = [
    "URS",
    "Risk Assessment",
    "Functional Specifications",
    "Test Scripts",
    "Traceability Matrix",
    "VSR",
    "Supplier Assessment",
]

ITEM_STATUSES = [
    "Draft",
    "In Review",
    "Approved",
    "Rejected",
    "Retired",
]

RELEASE_STATUSES = [
    "Planned",
    "In Progress",
    "Released",
    "Archived",
]

ITEM_TYPES = [
    "urs",
    "test_script",
    "risk",
    "traceability",
    "report",
    "note",
    "supplier_doc",
]


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class FolderItem:
    """
    A single artefact entry inside a release folder.

    :requirement: URS-30.1
    """

    item_id: str
    name: str
    item_type: str          # one of ITEM_TYPES
    status: str             # one of ITEM_STATUSES
    artifact_id: str        # optional link to EVOLV URS/TS id
    notes: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FolderItem":
        """Deserialise from plain dict."""
        return cls(**d)


@dataclass
class Release:
    """
    A versioned validation release containing GAMP 5 folders.

    :requirement: URS-30.2
    """

    release_id: str
    name: str
    version: str
    status: str
    description: str
    created_at: str
    folders: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=dict
    )

    # ── helpers ──────────────────────────────────────────────

    def get_items(
        self, folder: str
    ) -> List[FolderItem]:
        """Return FolderItem list for *folder*."""
        return [
            FolderItem.from_dict(d)
            for d in self.folders.get(folder, [])
        ]

    def add_item(
        self, folder: str, item: FolderItem
    ) -> None:
        """Append *item* to *folder*, creating it if needed."""
        if folder not in self.folders:
            self.folders[folder] = []
        self.folders[folder].append(item.to_dict())

    def remove_item(
        self, folder: str, item_id: str
    ) -> Optional[FolderItem]:
        """
        Remove and return the item with *item_id* from
        *folder*.  Returns None if not found.
        """
        items = self.folders.get(folder, [])
        for i, d in enumerate(items):
            if d.get("item_id") == item_id:
                removed = items.pop(i)
                return FolderItem.from_dict(removed)
        return None

    def item_count(self) -> int:
        """Total items across all folders."""
        return sum(
            len(v) for v in self.folders.values()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Release":
        """Deserialise from plain dict."""
        return cls(
            release_id=d["release_id"],
            name=d["name"],
            version=d["version"],
            status=d["status"],
            description=d.get("description", ""),
            created_at=d["created_at"],
            folders=d.get("folders", {}),
        )


@dataclass
class GlobalLibraryEntry:
    """
    A reusable artefact in the Global Library (System
    Descriptions or Risk Matrices).

    :requirement: URS-30.4
    """

    entry_id: str
    name: str
    entry_type: str   # "system_description" | "risk_matrix"
    content: str
    tags: List[str]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return asdict(self)

    @classmethod
    def from_dict(
        cls, d: Dict[str, Any]
    ) -> "GlobalLibraryEntry":
        """Deserialise from plain dict."""
        return cls(**d)


@dataclass
class Project:
    """
    Top-level project container.

    :requirement: URS-30.1
    """

    project_id: str
    name: str
    system_name: str
    compliance_mode: str
    description: str
    created_at: str
    releases: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )

    def get_release(
        self, release_id: str
    ) -> Optional[Release]:
        """Return Release by id or None."""
        d = self.releases.get(release_id)
        return Release.from_dict(d) if d else None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict."""
        return {
            "project_id":     self.project_id,
            "name":           self.name,
            "system_name":    self.system_name,
            "compliance_mode": self.compliance_mode,
            "description":    self.description,
            "created_at":     self.created_at,
            "releases":       self.releases,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Project":
        """Deserialise from plain dict."""
        return cls(
            project_id=d["project_id"],
            name=d["name"],
            system_name=d.get("system_name", ""),
            compliance_mode=d.get(
                "compliance_mode", "GMP"
            ),
            description=d.get("description", ""),
            created_at=d["created_at"],
            releases=d.get("releases", {}),
        )


# ─────────────────────────────────────────────────────────────
# ProjectStore singleton
# ─────────────────────────────────────────────────────────────

class ProjectStore:
    """
    Thread-safe, JSON-backed store for all project / release
    data and the Global Library.

    :requirement: URS-30.1
    :requirement: URS-30.3
    :requirement: URS-30.4
    """

    _instance: Optional["ProjectStore"] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._library: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load()

    @classmethod
    def get_instance(cls) -> "ProjectStore":
        """Return (or create) the singleton."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Projects ─────────────────────────────────────────────

    def create_project(
        self,
        name: str,
        system_name: str,
        compliance_mode: str = "GMP",
        description: str = "",
    ) -> Project:
        """
        Create and persist a new project.

        :param name: Human-readable project name.
        :param system_name: Name of the validated system.
        :param compliance_mode: GMP/GCP/GLP/ISO13485.
        :param description: Optional project description.
        :return: New Project instance.
        :requirement: URS-30.1
        """
        proj = Project(
            project_id=str(uuid.uuid4()),
            name=name,
            system_name=system_name,
            compliance_mode=compliance_mode,
            description=description,
            created_at=_now(),
        )
        with self._lock:
            self._projects[proj.project_id] = (
                proj.to_dict()
            )
            self._persist()
        return proj

    def get_project(
        self, project_id: str
    ) -> Optional[Project]:
        """Return Project by id or None."""
        d = self._projects.get(project_id)
        return Project.from_dict(d) if d else None

    def list_projects(self) -> List[Project]:
        """Return all projects sorted by creation date."""
        return sorted(
            [
                Project.from_dict(d)
                for d in self._projects.values()
            ],
            key=lambda p: p.created_at,
        )

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its releases.

        :param project_id: ID of the project to delete.
        :return: True if deleted, False if not found.
        :requirement: URS-30.1
        """
        with self._lock:
            if project_id not in self._projects:
                return False
            del self._projects[project_id]
            self._persist()
        return True

    # ── Releases ─────────────────────────────────────────────

    def create_release(
        self,
        project_id: str,
        name: str,
        version: str,
        description: str = "",
        status: str = "Planned",
        folder_template: Optional[List[str]] = None,
    ) -> Release:
        """
        Create a new release inside a project.

        Auto-populates GAMP 5 folder template unless a custom
        *folder_template* list is provided.

        :param project_id: Parent project ID.
        :param name: Release name (e.g. "v1.0 Validation").
        :param version: Version string (e.g. "1.0").
        :param description: Optional description.
        :param status: Initial release status.
        :param folder_template: Custom folder names list.
                                Defaults to GAMP5_FOLDERS.
        :return: New Release instance.
        :requirement: URS-30.2
        """
        folders_to_create = (
            folder_template
            if folder_template is not None
            else GAMP5_FOLDERS
        )
        rel = Release(
            release_id=str(uuid.uuid4()),
            name=name,
            version=version,
            status=status,
            description=description,
            created_at=_now(),
            folders={f: [] for f in folders_to_create},
        )
        with self._lock:
            proj_d = self._projects.get(project_id)
            if proj_d is None:
                raise KeyError(
                    f"Project '{project_id}' not found."
                )
            proj_d["releases"][rel.release_id] = (
                rel.to_dict()
            )
            self._persist()
        return rel

    def update_release_status(
        self,
        project_id: str,
        release_id: str,
        status: str,
    ) -> None:
        """
        Update the status field of a release.

        :requirement: URS-30.1
        """
        with self._lock:
            proj_d = self._projects.get(project_id)
            if proj_d is None:
                raise KeyError(
                    f"Project '{project_id}' not found."
                )
            rel_d = proj_d["releases"].get(release_id)
            if rel_d is None:
                raise KeyError(
                    f"Release '{release_id}' not found."
                )
            rel_d["status"] = status
            self._persist()

    # ── Items ─────────────────────────────────────────────────

    def add_item(
        self,
        project_id: str,
        release_id: str,
        folder: str,
        name: str,
        item_type: str = "urs",
        artifact_id: str = "",
        notes: str = "",
        status: str = "Draft",
    ) -> FolderItem:
        """
        Add an item to a folder inside a release.

        :param project_id: Parent project ID.
        :param release_id: Target release ID.
        :param folder: Folder name (must exist on release).
        :param name: Display name for the item.
        :param item_type: One of ITEM_TYPES.
        :param artifact_id: Optional EVOLV artefact ID.
        :param notes: Free-text notes.
        :param status: Initial item status.
        :return: New FolderItem instance.
        :requirement: URS-30.1
        """
        item = FolderItem(
            item_id=str(uuid.uuid4()),
            name=name,
            item_type=item_type,
            status=status,
            artifact_id=artifact_id,
            notes=notes,
            created_at=_now(),
            updated_at=_now(),
        )
        with self._lock:
            proj_d = self._projects[project_id]
            rel_d = proj_d["releases"][release_id]
            if folder not in rel_d["folders"]:
                rel_d["folders"][folder] = []
            rel_d["folders"][folder].append(
                item.to_dict()
            )
            self._persist()
        return item

    def move_item(
        self,
        project_id: str,
        src_release_id: str,
        src_folder: str,
        item_id: str,
        dst_release_id: str,
        dst_folder: str,
    ) -> FolderItem:
        """
        Move an item from one release/folder to another.

        Atomic under the write lock — the item is removed
        from the source and appended to the destination in
        a single operation.

        :param project_id: Parent project ID.
        :param src_release_id: Source release ID.
        :param src_folder: Source folder name.
        :param item_id: ID of the item to move.
        :param dst_release_id: Destination release ID.
        :param dst_folder: Destination folder name.
        :return: The moved FolderItem.
        :raises KeyError: If item not found at source.
        :requirement: URS-30.3
        """
        with self._lock:
            proj_d = self._projects[project_id]
            src_rel = proj_d["releases"][src_release_id]
            dst_rel = proj_d["releases"][dst_release_id]

            # Remove from source
            src_items = src_rel["folders"].get(
                src_folder, []
            )
            moved_d = None
            for i, d in enumerate(src_items):
                if d.get("item_id") == item_id:
                    moved_d = src_items.pop(i)
                    break
            if moved_d is None:
                raise KeyError(
                    f"Item '{item_id}' not found in "
                    f"'{src_folder}'."
                )

            # Update timestamp
            moved_d["updated_at"] = _now()

            # Append to destination
            if dst_folder not in dst_rel["folders"]:
                dst_rel["folders"][dst_folder] = []
            dst_rel["folders"][dst_folder].append(
                moved_d
            )
            self._persist()

        return FolderItem.from_dict(moved_d)

    def update_item_status(
        self,
        project_id: str,
        release_id: str,
        folder: str,
        item_id: str,
        status: str,
    ) -> None:
        """
        Update the status of an item in-place.

        :requirement: URS-30.1
        """
        with self._lock:
            proj_d = self._projects[project_id]
            rel_d = proj_d["releases"][release_id]
            for d in rel_d["folders"].get(folder, []):
                if d.get("item_id") == item_id:
                    d["status"] = status
                    d["updated_at"] = _now()
                    break
            self._persist()

    def delete_item(
        self,
        project_id: str,
        release_id: str,
        folder: str,
        item_id: str,
    ) -> bool:
        """
        Delete an item from a folder.

        :return: True if deleted, False if not found.
        :requirement: URS-30.1
        """
        with self._lock:
            proj_d = self._projects.get(project_id, {})
            rel_d = (
                proj_d.get("releases", {}).get(
                    release_id, {}
                )
            )
            items = rel_d.get("folders", {}).get(
                folder, []
            )
            for i, d in enumerate(items):
                if d.get("item_id") == item_id:
                    items.pop(i)
                    self._persist()
                    return True
        return False

    # ── Global Library ────────────────────────────────────────

    def add_library_entry(
        self,
        name: str,
        entry_type: str,
        content: str,
        tags: Optional[List[str]] = None,
    ) -> GlobalLibraryEntry:
        """
        Add a reusable entry to the Global Library.

        :param name: Entry name.
        :param entry_type: "system_description" or
                           "risk_matrix".
        :param content: Text / JSON content.
        :param tags: Optional list of tag strings.
        :return: New GlobalLibraryEntry.
        :requirement: URS-30.4
        """
        entry = GlobalLibraryEntry(
            entry_id=str(uuid.uuid4()),
            name=name,
            entry_type=entry_type,
            content=content,
            tags=tags or [],
            created_at=_now(),
            updated_at=_now(),
        )
        with self._lock:
            self._library.append(entry.to_dict())
            self._persist()
        return entry

    def list_library(
        self,
        entry_type: Optional[str] = None,
    ) -> List[GlobalLibraryEntry]:
        """
        Return Global Library entries, optionally filtered
        by *entry_type*.

        :requirement: URS-30.4
        """
        entries = [
            GlobalLibraryEntry.from_dict(d)
            for d in self._library
        ]
        if entry_type:
            entries = [
                e for e in entries
                if e.entry_type == entry_type
            ]
        return entries

    def delete_library_entry(
        self, entry_id: str
    ) -> bool:
        """
        Delete a Global Library entry.

        :requirement: URS-30.4
        """
        with self._lock:
            for i, d in enumerate(self._library):
                if d.get("entry_id") == entry_id:
                    self._library.pop(i)
                    self._persist()
                    return True
        return False

    # ── Persistence ───────────────────────────────────────────

    def _persist(self) -> None:
        """Write current state to disk (call inside lock)."""
        _STORE_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        payload = {
            "projects": self._projects,
            "library":  self._library,
        }
        _STORE_PATH.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        """Load state from disk on startup."""
        if not _STORE_PATH.exists():
            return
        try:
            data = json.loads(
                _STORE_PATH.read_text(encoding="utf-8")
            )
            self._projects = data.get("projects", {})
            self._library = data.get("library", [])
        except Exception:
            pass  # corrupt file — start fresh


# ─────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────

def _now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()
