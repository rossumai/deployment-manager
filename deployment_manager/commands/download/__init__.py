# Optional - preload types if you want to force-run model_rebuild in a single place
from .directory import DownloadOrganizationDirectory
from .saver import (
    EmailTemplateSaver,
    FormulaSaver,
    HookSaver,
    InboxSaver,
    QueueSaver,
    RuleSaver,
    SchemaSaver,
    WorkspaceSaver,
)

DownloadOrganizationDirectory.model_rebuild()
WorkspaceSaver.model_rebuild()
QueueSaver.model_rebuild()
EmailTemplateSaver.model_rebuild()
InboxSaver.model_rebuild()
SchemaSaver.model_rebuild()
FormulaSaver.model_rebuild()
RuleSaver.model_rebuild()
HookSaver.model_rebuild()
