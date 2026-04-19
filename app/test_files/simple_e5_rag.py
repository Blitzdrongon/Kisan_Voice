from pathlib import Path
from services.rag_e5_groq import E5RAGSystem

rag = E5RAGSystem()

json_path = Path(
    "/home/oem/KisanVoice_v2/KisanVoice/rag/final_clean_merged_dataset (1).json"
)

rag.add_json(str(json_path))

print(
    rag.chat(
        "ಪ್ರತಿ ಏಕರೆಗೆ ಬೇಕಾಗುವ ಬೀಜ ಕಬ್ಬಿನ ಪ್ರಮಾಣ ಎಷ್ಟು?",
        show_context=False
    )
)
