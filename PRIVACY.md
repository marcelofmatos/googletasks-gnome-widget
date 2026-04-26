# Política de Privacidade — Google Tasks Widget

**Última atualização:** 26 de abril de 2026

Esta Política de Privacidade descreve como o aplicativo **Google Tasks Widget**
("o Aplicativo", "nós") trata as informações do usuário ao acessar a Google
Tasks API.

O Aplicativo é um software open source distribuído gratuitamente, executado
localmente no computador do usuário (widget de desktop para GNOME). Não há
servidor remoto operado pelos desenvolvedores e nenhum dado do usuário é
transmitido para terceiros.

## 1. Informações que o Aplicativo acessa

Ao autorizar o Aplicativo via OAuth2, ele obtém acesso ao seguinte escopo da
sua Conta Google:

- `https://www.googleapis.com/auth/tasks` — leitura e modificação das suas
  listas e tarefas no Google Tasks.

Com esse escopo, o Aplicativo lê:

- Nomes e identificadores das suas listas de tarefas
- Títulos, status, datas de vencimento e identificadores das suas tarefas

E pode escrever:

- Marcação de tarefas como concluídas (ação iniciada explicitamente pelo
  usuário ao clicar no botão de concluir)

O Aplicativo **não acessa** sua caixa de e-mail, contatos, agenda, arquivos do
Drive, perfil completo ou qualquer outro dado fora do escopo `tasks`.

## 2. Como as informações são utilizadas

As informações obtidas são utilizadas exclusivamente para:

- Exibir suas tarefas pendentes na interface do widget
- Permitir que você marque tarefas como concluídas a partir do widget
- Abrir o Google Tasks no navegador quando você clica em uma tarefa

Os dados são processados em memória, no seu próprio computador, apenas
durante a execução do widget.

## 3. Armazenamento local

O Aplicativo armazena os seguintes arquivos no diretório
`~/.config/googletasks-widget/` do seu sistema:

- `credentials.json` — credenciais OAuth2 do projeto Google Cloud que você
  mesmo criou e baixou
- `token.json` — token de acesso OAuth2 emitido pelo Google após a sua
  autorização, utilizado para renovar o acesso sem solicitar nova
  autenticação

Esses arquivos ficam **somente no seu computador**. Eles nunca são enviados
para os desenvolvedores nem para qualquer outro destino além dos servidores
oficiais do Google durante as chamadas autenticadas à API.

Os títulos e metadados das tarefas obtidos da API **não são gravados em
disco** pelo Aplicativo — permanecem apenas em memória durante a execução.

## 4. Compartilhamento com terceiros

O Aplicativo **não compartilha, vende ou transfere** nenhuma informação do
usuário para terceiros. A única comunicação de rede realizada pelo
Aplicativo é com os endpoints oficiais do Google necessários para
autenticação OAuth2 e para a Google Tasks API.

## 5. Cookies e rastreamento

O Aplicativo **não utiliza cookies, analytics, telemetria, crash reporting**
ou qualquer outro mecanismo de rastreamento.

## 6. Conformidade com a Política de Dados de Usuário do Google

O uso e a transferência de informações recebidas das APIs do Google por este
Aplicativo aderem à
[Política de Dados de Usuário dos Serviços de API do Google](https://developers.google.com/terms/api-services-user-data-policy),
incluindo os requisitos de Uso Limitado.

## 7. Revogação de acesso

Você pode revogar o acesso do Aplicativo à sua Conta Google a qualquer
momento em
[https://myaccount.google.com/permissions](https://myaccount.google.com/permissions).

Para remover completamente os dados locais, basta apagar o diretório:

```bash
rm -rf ~/.config/googletasks-widget/
```

## 8. Segurança

Os arquivos de credenciais e token ficam protegidos pelas permissões padrão
do sistema de arquivos do seu usuário. Recomenda-se não compartilhar esses
arquivos com terceiros, pois eles concedem acesso à sua conta do Google
Tasks.

## 9. Privacidade de menores

O Aplicativo não é direcionado a menores de 13 anos e não coleta
intencionalmente nenhuma informação dessa faixa etária.

## 10. Alterações nesta Política

Atualizações desta Política serão publicadas no repositório oficial do
projeto. A data da última revisão consta no topo deste documento.

## 11. Contato

Dúvidas sobre esta Política de Privacidade podem ser enviadas para:

- E-mail: claude@marcelomatos.dev
- Repositório: <https://github.com/marcelofmatos/googletasks-gnome-widget>
