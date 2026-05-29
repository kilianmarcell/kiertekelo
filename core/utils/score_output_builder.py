def _clean_report_text(value: str) -> str:
    if not isinstance(value, str):
        return ""

    cleaned = value.replace("\\n", " ").replace("\n", " ").replace("\r", " ")
    return " ".join(cleaned.split())

def build_score_report_lines(
    student_name: str, 
    evaluation_text: str, 
    score: int,
    percentage: int = None,
    manual_aligned_score: float | None = None,
) -> list[str]:
    lines = []
    lines.append(f"ÉRTÉKELÉS: {student_name}")
    lines.append("")
    
    if percentage is not None:
        lines.append(f"TELJESÍTÉS: {percentage}%")
        lines.append("")

    if manual_aligned_score is not None:
        lines.append(f"MAN-KALIBRÁLT PONT: {manual_aligned_score:.1f}/3")
        lines.append("")
    
    lines.append(f"PONTSZÁM: {score:.1f}/5.0")
    lines.append("")
    
    clean_eval = _clean_report_text(evaluation_text)
    lines.append(f"ÉRTÉKELÉS: {clean_eval}")
    
    lines.append("")
    if percentage is not None:
        lines.append(f"VÉGSŐ SZÁZALÉK: {percentage}%")
    
    return lines
