from app.schemas.reading_session import FeelingValue
from app.schemas.reading_trajectory import TrajectoryLabel


def build_closing_text(
    total_sessions: int,
    trajectory_label: TrajectoryLabel | None,
    dominant_feeling: FeelingValue | None,
    last_feedback_text: str | None,
) -> str:
    if total_sessions <= 2:
        return "Foi uma travessia breve, ainda em formação, mas já com sinais de abertura."

    if trajectory_label == "continuity":
        return "Essa leitura encontrou um ritmo próprio e chegou ao fim com continuidade viva."

    if trajectory_label == "resistance":
        return "Foi um percurso mais exigente, mas algo se consolidou ao longo do caminho."

    if trajectory_label == "assimilation":
        return "A leitura pediu tempo e decantação, e terminou com um corpo mais firme."

    if trajectory_label == "oscillating":
        return "A leitura oscilou em alguns momentos, mas deixou um traço claro no percurso."

    if last_feedback_text and any(token in last_feedback_text.lower() for token in ("abriu", "aberto", "aberta")):
        return "O percurso chegou ao fim com um sinal discreto de abertura."

    if dominant_feeling == "empolgante":
        return "A leitura terminou com uma energia viva, como quem fecha um percurso ainda aceso."

    if dominant_feeling == "travada":
        return "Mesmo mais contido, esse percurso encontrou uma forma própria de se encerrar."

    return "Esse percurso chegou ao fim preservando o traço que ganhou ao longo da leitura."
