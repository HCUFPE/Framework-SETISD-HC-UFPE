# Diretrizes de Git e Integração do Projeto

- **Fluxo de Trabalho de Branching**: Nunca faça merges diretos ou pushes nas branches principais (`develop`, `master`, `main`) pelo terminal do agente. 
- **Nova Funcionalidade / Correção**: Crie sempre uma branch separada a partir da `develop` mais recente para realizar qualquer alteração.
- **Integração**: Ao finalizar a implementação na branch de funcionalidade, instrua o usuário a abrir um Pull Request (PR) no GitHub para que a equipe possa revisar e aprovar o merge na `develop`. Ao fazer isso, apresente um rascunho para a descrição do PR seguindo rigorosamente o template definido em [.github/PULL_REQUEST_TEMPLATE.md](file:///c:/Users/ado1/OneDrive/Documentos/HC-PathLab-Analytics/.github/PULL_REQUEST_TEMPLATE.md).
