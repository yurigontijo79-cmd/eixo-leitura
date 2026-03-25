from app.schemas.reading_session import FeelingValue

FEEDBACK_OPTIONS_BY_FEELING: dict[FeelingValue, list[str]] = {
    "fluida": [
        "A leitura parece ter fluído com naturalidade.",
        "Hoje a leitura parece ter encontrado um ritmo sereno.",
        "Há sinal de um avanço leve e contínuo aqui.",
    ],
    "empolgante": [
        "Há um sinal claro de interesse crescente aqui.",
        "Essa leitura parece ter acendido vontade de seguir adiante.",
        "O texto parece ter ganho força no seu percurso de hoje.",
    ],
    "travada": [
        "Pode valer desacelerar e revisitar esse trecho.",
        "Talvez essa parte tenha pedido mais fôlego do que o esperado.",
        "Talvez seja melhor voltar a esse ponto com menos pressa.",
    ],
    "confusa": [
        "Talvez esse ponto mereça uma segunda leitura.",
        "Pode ser bom retomar esse trecho com mais calma depois.",
        "Ainda parece haver algo pedindo uma volta cuidadosa aqui.",
    ],
    "densa": [
        "Esse tipo de leitura costuma exigir mais tempo de assimilação.",
        "Talvez essa leitura precise mesmo de um passo mais lento.",
        "Há leituras que rendem melhor quando recebem mais tempo de decantação.",
    ],
}

KEYWORD_VARIATIONS: list[tuple[list[str], list[str]]] = [
    (
        ["curios", "vontade de continuar", "seguir"],
        [
            "Você parece ter encontrado algo que puxou sua curiosidade.",
            "Há um ponto dessa leitura que claramente te chamou para continuar.",
            "Parece que a leitura deixou uma vontade viva de seguir em frente.",
        ],
    ),
    (
        ["trav", "difícil", "pesad", "nublado"],
        [
            "Talvez esse trecho tenha exigido mais esforço do que o normal.",
            "Esse ponto parece ter pedido mais insistência da sua parte.",
            "Há sinal de atrito aqui, como se a leitura tivesse segurado um pouco mais.",
        ],
    ),
    (
        ["claro", "abriu", "aceso"],
        [
            "Parece que algo dessa leitura ficou vivo em você hoje.",
            "Há um ponto dessa leitura que parece ter se aberto melhor agora.",
            "Alguma coisa parece ter encontrado mais nitidez neste trecho.",
        ],
    ),
]

def _pick_variation(
    options: list[str],
    recent_feedback_texts: list[str],
    cycle_index: int,
) -> str:
    immediate_previous = recent_feedback_texts[0] if recent_feedback_texts else None
    available_options = [option for option in options if option != immediate_previous] or options

    recency_by_text: dict[str, int] = {}
    usage_by_text: dict[str, int] = {}
    for position, feedback_text in enumerate(recent_feedback_texts):
        usage_by_text[feedback_text] = usage_by_text.get(feedback_text, 0) + 1
        recency_by_text.setdefault(feedback_text, position)

    rotated_indices = {
        option: (index - cycle_index) % len(available_options)
        for index, option in enumerate(available_options)
    }

    return min(
        available_options,
        key=lambda option: (
            0 if option not in usage_by_text else 1,
            usage_by_text.get(option, 0),
            recency_by_text.get(option, len(recent_feedback_texts) + 1),
            rotated_indices[option],
        ),
    )


def build_feedback_text(
    feeling: FeelingValue,
    reflection_answers: list[str],
    recent_feedback_texts: list[str],
    cycle_index: int = 0,
) -> str:
    joined_answers = " ".join(answer.lower() for answer in reflection_answers)

    for keywords, options in KEYWORD_VARIATIONS:
        if any(token in joined_answers for token in keywords):
            return _pick_variation(options, recent_feedback_texts, cycle_index)

    return _pick_variation(FEEDBACK_OPTIONS_BY_FEELING[feeling], recent_feedback_texts, cycle_index)
