from rag_dnd.config import Config
from rag_dnd.rag.database import get_session, init_db
from rag_dnd.rag.models import CampaignMetadata

config = Config.load()
init_db()

session = get_session()
campaign = CampaignMetadata(
    full_name="Lost Mine of Phandelver / Tyranny of Dragons",
    short_name="lmop_tod",
    system="D&D 5e",
    language="Dutch",
    active_summary_file="data/summary.md",
    session_log_file="data/LMoP_ToD_TimJansma_Log.md",
    extensions={}
)
session.add(campaign)
session.commit()
print(f"Campaign '{campaign.short_name}' created with id {campaign.id}")
