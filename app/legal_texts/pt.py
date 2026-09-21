"""Portuguese legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Português",
    "dir": "ltr",
    "updated_label": "Última atualização",
    "updated": "14 de julho de 2026",
    "contact_label": "Contato",
    "languages_label": "Idioma",
    "translation_notice": (
        "Esta tradução é fornecida apenas por conveniência. Em caso de conflito, "
        "prevalece a versão em turco."
    ),
    "privacy": {
        "title": "Política de Privacidade",
        "note": (
            "<strong>Resumo:</strong> Usamos seus dados apenas para criar conteúdo personalizado "
            "de astrologia e leitura da sorte para você. As fotos de leitura de borra de café, da "
            "mão ou do rosto que você envia são <strong>excluídas imediatamente após a "
            "análise</strong> e não são armazenadas. Não vendemos seus dados a terceiros. Você pode "
            "excluir completamente seu histórico e sua conta pelo próprio aplicativo quando quiser."
        ),
        "sections": [
            ("Dados que coletamos", [
                "Conta: endereço de e-mail (por meio do Supabase Auth). Perfil: seu nome (opcional), "
                "data/hora/local de nascimento e suas preferências de idioma e interesses. Conteúdo: as "
                "análises que você gera (mapa astral, tarô, leituras, compatibilidade amorosa), seu "
                "histórico de conversas com a inteligência artificial e os registros de contexto "
                "formados por resumos curtos desses itens (Cosmic Memory).",
            ]),
            ("Fotos", [
                "As fotos que você envia para leitura de borra de café, da mão ou do rosto são "
                "processadas no servidor somente durante a análise e são <strong>excluídas "
                "permanentemente assim que a análise termina</strong>. As fotos não são armazenadas; "
                "no arquivo são mantidos apenas o resultado em texto e a lista de símbolos.",
            ]),
            ("Como seus dados são tratados", [
                "Os cálculos astrológicos são feitos em nosso servidor (Swiss Ephemeris). Para as "
                "interpretações personalizadas, seu conteúdo é enviado a provedores de inteligência "
                "artificial (OpenAI e Google Gemini) exclusivamente para gerar interpretações. As chaves "
                "de API ficam somente no servidor; elas não estão presentes no aplicativo.",
            ]),
            ("Retenção e exclusão", [
                "Você pode excluir seus dados a qualquer momento: em <em>Perfil → Meus dados → Apagar "
                "memória / histórico</em> você pode remover seu histórico de análises e de conversas; em "
                "<em>Excluir conta permanentemente</em> você pode remover permanentemente todos os seus "
                "dados e sua conta. Quando uma conta é excluída, todos os registros associados são "
                "excluídos de forma irreversível.",
            ]),
            ("Compartilhamento", [
                "Não vendemos nem alugamos seus dados para fins publicitários. Nós os tratamos apenas com "
                "os provedores de infraestrutura necessários para prestar o serviço (autenticação, banco "
                "de dados, interpretação por inteligência artificial, gestão de assinaturas).",
            ]),
            ("Exercício dos seus direitos (KVKK/GDPR)", [
                "Você tem o direito de acessar, corrigir e excluir seus dados e de limitar o seu "
                "tratamento. Para fazer sua solicitação, você pode escrever para {contact_link}.",
            ]),
            ("Crianças", [
                "O Astrype não se destina a usuários menores de 13 anos.",
            ]),
            ("Código aberto", [
                "O código-fonte do software de servidor do Astrype está disponível publicamente sob a "
                "licença {license}: {source_link}. O código-fonte não contém nenhum dado de usuário nem "
                "chaves secretas.",
            ]),
        ],
    },
    "terms": {
        "title": "Termos de Uso",
        "note": (
            "<strong>Importante:</strong> As interpretações de astrologia, tarô, leitura de borra de "
            "café, da mão ou do rosto e de sonhos no Astrype são <strong>apenas para entretenimento e "
            "reflexão pessoal</strong>. Elas não substituem o apoio profissional em decisões médicas, "
            "jurídicas, financeiras ou críticas para a segurança. Seu guia de inteligência artificial "
            "(Lyra) não faz afirmações definitivas sobre o destino ou o futuro."
        ),
        "sections": [
            ("Natureza do serviço", [
                "O Astrype oferece mapa astral, interpretações diárias/mensais, tarô, módulos de leitura "
                "da sorte e um assistente de conversa com inteligência artificial que conhece seu "
                "histórico. O conteúdo destina-se à reflexão e ao autoconhecimento; não pretende ser uma "
                "verdade científica ou definitiva.",
            ]),
            ("Isenção de responsabilidade", [
                "Você é responsável pelas decisões que tomar com base nas interpretações do aplicativo. "
                "Em situações de saúde, jurídicas, financeiras ou de crise, procure um profissional "
                "especializado.",
            ]),
            ("Assinatura", [
                "Os recursos Premium exigem uma assinatura. Pagamento, renovação e cancelamento são "
                "gerenciados pela Apple App Store ou pelo Google Play. A assinatura é renovada "
                "automaticamente, a menos que você a cancele antes do fim do período; você pode cancelar "
                "pela sua conta da loja. As compras podem ser restauradas com \"Restaurar compras\".",
            ]),
            ("Uso aceitável", [
                "Você não pode usar o serviço para fins ilegais, de forma que viole os direitos de "
                "terceiros ou abusando do sistema.",
            ]),
            ("Alterações", [
                "Podemos atualizar estes termos periodicamente. Anunciaremos as alterações importantes "
                "dentro do aplicativo.",
            ]),
            ("Código aberto / Código-fonte", [
                "O software de servidor (backend) do Astrype é de código aberto e é publicado sob a "
                "licença <strong>{license}</strong>. Todo usuário que interage com este serviço por meio "
                "de uma rede pode acessar gratuitamente o código-fonte completo do software que executa o "
                "serviço, examiná-lo, modificá-lo e redistribuí-lo nos termos da licença:",
                "{source_link}",
                "Link permanente: {source_path_link}. Os cálculos astrológicos utilizam a biblioteca "
                "Swiss Ephemeris da Astrodienst AG (com a opção AGPL) e o Kerykeion; as licenças de "
                "terceiros estão listadas no arquivo <code>THIRD_PARTY_LICENSES.md</code> do repositório. "
                "A licença declara que o software é fornecido \"no estado em que se encontra\" e sem "
                "qualquer garantia. Esta seção abrange apenas o código-fonte do software de servidor; o "
                "nome e o logotipo do Astrype não constituem um direito de uso de marca concedido por "
                "esta licença.",
            ]),
            ("Contato", [
                "Para dúvidas: {contact_link}",
            ]),
        ],
    },
}
