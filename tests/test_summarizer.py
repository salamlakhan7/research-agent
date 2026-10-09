from app.services.summarizer import summarize_local, synthesize_groq

text = (
    "Large language models are being adopted in hospitals to help doctors "
    "summarize patient notes, draft discharge letters, and reduce paperwork. "
    "Studies show clinicians save significant time, but concerns remain about "
    "hallucinated facts, patient privacy, and unclear regulation. "
) * 6

local = summarize_local(text)
print("LOCAL:", local, "\n")

brief = synthesize_groq(
    "LLMs in healthcare",
    [("a.com", local)],
    length="short",
    style="bullets",
)
print("GROQ:", brief)