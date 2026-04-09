"""Enums for the game module."""
from enum import Enum, unique


@unique
class CharacterType(str, Enum):
    """
    Character type enum.
    
    PC: Player character
    PARTY_MEMBER: Party member
    NPC: Non-player character
    PASSERBY: Passerby
    MONSTER: Monster
    """
    PC = "pc"
    PARTY_MEMBER = "party_member"
    NPC = "npc"
    PASSERBY = "passerby"
    MONSTER = "monster"


@unique
class Disposition(str, Enum):
    """
    Disposition enum.
    
    FRIENDLY: Friendly
    NEUTRAL: Neutral
    HOSTILE: Hostile
    UNKNOWN: Unknown
    """
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    UNKNOWN = "unknown"


@unique
class RelationshipType(str, Enum):
    """
    Relationship type enum.

    ALLY: Ally
    RIVAL: Rival
    ACQUAINTANCE: Acquaintance
    FRIEND: Friend
    FAMILY: Family
    PARENT: Parent
    CHILD: Child
    SIBLING: Sibling
    SPOUSE: Spouse
    EX_SPOUSE: Ex-spouse
    LOVER: Lover
    EX_LOVER: Ex-lover
    COLLEAGUE: Colleague
    EMPLOYER: Employer
    EMPLOYEE: Employee
    BUSINESS_PARTNER: Business partner
    FRIEND_WITH_BENEFITS: Friend with benefits
    ENEMY: Enemy
    MENTOR: Mentor
    APPRENTICE: Apprentice
    DEITY: Deity
    WORSHIPPER: Worshipper
    SERVANT: Servant
    PATRON: Patron
    WARLOCK: Warlock
    CAPTOR: Captor
    PRISONER: Prisoner
    SLAVE: Slave
    MASTER: Master
    NEUTRAL: Neutral
    GUARDIAN: Guardian
    WARD: Ward
    CREATOR: Creator
    CREATION: Creation
    PET: Pet
    VICTIM: Victim
    PERPETRATOR: Perpetrator
    SAVIOR: Savior
    RESCUEE: Rescuee
    HANDLER: Handler
    INFORMANT: Informant
    DEBTOR: Debtor
    CREDITOR: Creditor
    IDOL: Idol
    FAN: Fan
    """
    ALLY = "ally"
    RIVAL = "rival"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    FAMILY = "family"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    SPOUSE = "spouse"
    EX_SPOUSE = "ex_spouse"
    LOVER = "lover"
    EX_LOVER = "ex_lover"
    COLLEAGUE = "colleague"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    BUSINESS_PARTNER = "business_partner"
    FRIEND_WITH_BENEFITS = "friend_with_benefits"
    ENEMY = "enemy"
    MENTOR = "mentor"
    APPRENTICE = "apprentice"
    DEITY = "deity"
    WORSHIPPER = "worshipper"
    SERVANT = "servant"
    PATRON = "patron"
    WARLOCK = "warlock"
    CAPTOR = "captor"
    PRISONER = "prisoner"
    SLAVE = "slave"
    MASTER = "master"
    NEUTRAL = "neutral"
    GUARDIAN = "guardian"
    WARD = "ward"
    CREATOR = "creator"
    CREATION = "creation"
    PET = "pet"
    VICTIM = "victim"
    PERPETRATOR = "perpetrator"
    SAVIOR = "savior"
    RESCUEE = "rescuee"
    HANDLER = "handler"
    INFORMANT = "informant"
    DEBTOR = "debtor"
    CREDITOR = "creditor"
    IDOL = "idol"
    FAN = "fan"
    

@unique
class AssetType(str, Enum):
    """
    Asset type enum.

    IMAGE: Image
    VIDEO: Video
    AUDIO: Audio
    TEXT: Text
    MAP: Map
    DOCUMENT: Document
    GRAPH: Graph
    TABLE: Table
    OTHER: Other
    """
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    MAP = "map"
    DOCUMENT = "document"
    GRAPH = "graph"
    TABLE = "table"
    OTHER = "other"


@unique
class PlayerType(str, Enum):
    """Player type enum.

    HUMAN: Human
    AI: AI
    """
    HUMAN = "human"
    AI = "ai"
