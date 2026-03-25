from app.schemas.book import Book

MOCK_BOOKS = [
    Book(
        id=1,
        title="A Morte de Ivan Ilitch",
        author="Liev Tolstói",
        description="Uma leitura breve e incisiva sobre rotina, finitude e o choque de acordar tarde para a própria vida.",
    ),
    Book(
        id=2,
        title="Quarto de Despejo",
        author="Carolina Maria de Jesus",
        description="O registro diário de uma consciência atenta que transforma sobrevivência em observação aguda do mundo.",
    ),
    Book(
        id=3,
        title="A Hora da Estrela",
        author="Clarice Lispector",
        description="Um romance de poucas páginas e enorme densidade sobre presença, invisibilidade e linguagem.",
    ),
    Book(
        id=4,
        title="Bartleby, o Escrivão",
        author="Herman Melville",
        description="Uma narrativa enxuta sobre recusa, estranhamento e o vazio que desafia qualquer mediação simples.",
    ),
]
