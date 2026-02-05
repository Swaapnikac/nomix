from dataclasses import dataclass
import tiktoken

@dataclass
class Chunk:
    text: str
    start_token: int
    end_token: int

def chunk_by_tokens(
    text: str,
    chunk_tokens: int = 550,
    overlap_tokens: int = 90,
    tokenizer_model: str = "gpt-4o-mini",
) -> list[Chunk]:
    enc = tiktoken.encoding_for_model(tokenizer_model)
    toks = enc.encode(text)

    chunks = []
    i = 0
    n = len(toks)
    while i < n:
        j = min(i + chunk_tokens, n)
        piece = enc.decode(toks[i:j]).strip()
        if piece:
            chunks.append(Chunk(text=piece, start_token=i, end_token=j))
        i = max(j - overlap_tokens, i + 1)
    return chunks