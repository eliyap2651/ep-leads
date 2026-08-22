import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SALES_MANAGER = "sales_manager"
    SALES_AGENT = "sales_agent"
    VIEWER = "viewer"


class Confidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecordType(str, enum.Enum):
    TENDER = "tender"
    PROJECT = "project"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    CONTACTED = "contacted"
    INFO_SENT = "info_sent"
    QUOTE_SENT = "quote_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NOT_RELEVANT = "not_relevant"
    NO_RESPONSE = "no_response"


class LeadTier(str, enum.Enum):
    HOT = "hot"       # 90-100
    HIGH = "high"      # 75-89
    MEDIUM = "medium"  # 55-74
    LOW = "low"        # 0-54


class Domain(str, enum.Enum):
    HOTEL = "hotel"
    SCHOOL = "school"
    KINDERGARTEN = "kindergarten"
    YESHIVA = "yeshiva"
    DORMITORY = "dormitory"
    NURSING_HOME = "nursing_home"
    ASSISTED_LIVING = "assisted_living"
    HOSPITAL = "hospital"
    UNIVERSITY = "university"
    MUNICIPALITY = "municipality"
    GOV_COMPANY = "gov_company"
    FACTORY = "factory"
    OFFICE = "office"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    COMMUNITY_CENTER = "community_center"
    HALL = "hall"
    HOSPITALITY = "hospitality"
    OTHER = "other"


class Region(str, enum.Enum):
    NORTH = "north"
    HAIFA = "haifa"
    VALLEYS = "valleys"
    CENTER = "center"
    SHARON = "sharon"
    TEL_AVIV = "tel_aviv"
    JERUSALEM = "jerusalem"
    SHFELA = "shfela"
    SOUTH = "south"
    EILAT = "eilat"
    UNKNOWN = "unknown"


class SourceType(str, enum.Enum):
    HTML = "html"
    API = "api"
    RSS = "rss"
    SITEMAP = "sitemap"
    MANUAL = "manual"


class ScanFrequency(str, enum.Enum):
    HOURLY = "hourly"
    EVERY_3H = "every_3h"
    EVERY_6H = "every_6h"
    EVERY_12H = "every_12h"
    DAILY = "daily"
    WEEKLY = "weekly"
    NONE = "none"


class SourceStatus(str, enum.Enum):
    OK = "ok"
    ERROR = "error"
    PENDING = "pending"
    DISABLED = "disabled"


class ScanRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class AlertType(str, enum.Enum):
    NEW_LEAD = "new_lead"
    NEW_TENDER = "new_tender"
    TENDER_OPENED = "tender_opened"
    TENDER_CLOSING_SOON = "tender_closing_soon"
    TENDER_CHANGED = "tender_changed"
    DEADLINE_CHANGED = "deadline_changed"
    NEW_PROJECT = "new_project"
    NEW_CONTACT = "new_contact"
    HIGH_SCORE = "high_score"


class AlertChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    PUSH = "push"
    SMS = "sms"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    HTML = "html"
    OTHER = "other"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class ProjectStage(str, enum.Enum):
    PLANNING = "planning"
    APPROVAL = "approval"
    CONSTRUCTION = "construction"
    RENOVATION = "renovation"
    PRE_PROCUREMENT = "pre_procurement"
