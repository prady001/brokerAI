"""
Adapter de e-mail para seguradoras que enviam extratos de comissão por e-mail.
Acessa caixa IMAP da corretora, filtra e-mails da seguradora e extrai anexos.
"""
import imaplib

from agents.commissioning.portal_adapters.base import InsurerAdapter


class EmailAdapter(InsurerAdapter):
    """
    Adapter para seguradoras que enviam extratos de comissão por e-mail.

    Configuração esperada em credentials:
        imap_host:     servidor IMAP (ex: imap.gmail.com)
        imap_port:     porta IMAP (padrão: 993)
        email:         endereço da caixa da corretora
        password:      senha ou app-password
        sender_filter: endereço ou domínio remetente da seguradora
        subject_filter: substring do assunto esperado (ex: "Extrato de Comissão")
        attachment_types: extensões aceitas (ex: ["pdf", "xlsx"])
    """

    def __init__(self, insurer_id: str, credentials: dict) -> None:
        super().__init__(insurer_id, credentials)
        self._client: imaplib.IMAP4_SSL | None = None

    async def login(self) -> bool:
        """
        Conecta ao servidor IMAP e faz login com as credenciais da corretora.
        Retorna True se a conexão for estabelecida com sucesso.
        """
        raise NotImplementedError

    async def fetch_commissions(self) -> list[dict]:
        """
        Filtra e-mails não lidos do remetente configurado (sender_filter)
        com o assunto esperado (subject_filter).

        Para cada e-mail encontrado:
        1. Baixa o(s) anexo(s) (PDF ou planilha)
        2. Faz upload para S3 via upload_document
        3. Extrai dados estruturados via OCR (Mistral OCR ou Textract)

        Retorna lista de comissões no formato padrão:
        [{ insurer: str, amount: str, reference_month: str,
           raw_file_url: str, extracted_at: str }]
        """
        raise NotImplementedError

    async def logout(self) -> None:
        """Fecha a conexão IMAP."""
        raise NotImplementedError
