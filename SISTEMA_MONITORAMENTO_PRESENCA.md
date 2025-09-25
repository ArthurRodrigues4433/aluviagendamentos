# Sistema de Monitoramento de Presença de Clientes

## Visão Geral

O sistema implementa um monitoramento automático de presença de clientes para agendamentos, garantindo que o dono do estabelecimento seja notificado quando um cliente não comparece no horário agendado.

## Funcionalidades Implementadas

### 1. Monitoramento Automático
- **Verificação contínua**: A cada 30 segundos, o sistema verifica agendamentos próximos (próximas 2 horas)
- **Detecção de atraso**: Identifica quando já se passaram 20 minutos do horário agendado sem confirmação de presença
- **Status monitorado**: Apenas agendamentos com status 'agendado' são monitorados

### 2. Sistema de Notificações
- **Notificações visuais**: Aparecem no canto superior direito da tela
- **Alertas sonoros**: Beep simples quando uma notificação é exibida
- **Modal de confirmação**: Interface dedicada para confirmar presença
- **Countdown visual**: Mostra tempo restante para resposta (5 minutos)

### 3. Ações Disponíveis
- **✅ Cliente Apareceu**: Confirma presença e muda status para 'confirmado'
- **❌ Cliente Não Apareceu**: Registra ausência e muda status para 'nao_compareceu'
- **Timeout automático**: Após 5 minutos sem resposta, registra ausência automaticamente

### 4. Status de Agendamento
- **agendado**: Agendamento criado, aguardando execução
- **confirmado**: Cliente confirmou presença
- **concluido**: Serviço realizado com sucesso
- **cancelado**: Agendamento cancelado
- **nao_compareceu**: Cliente não compareceu (novo status)

### 5. Limpeza Automática
- **Execução diária**: Remove agendamentos 'nao_compareceu' com mais de 2 dias
- **Preservação de dados**: Mantém histórico recente para análise
- **Otimização**: Mantém banco de dados limpo e performático
- **Configurável**: Período de retenção pode ser ajustado

### 6. Estatísticas Filtradas
- **Dashboard inteligente**: Mostra apenas agendamentos ativos (status 'agendado')
- **Exclusão automática**: Remove 'nao_compareceu', 'cancelado' das métricas
- **Precisão**: Métricas refletem apenas agendamentos válidos e pendentes
- **Atualização em tempo real**: Interface responde imediatamente às mudanças

## Como Funciona

### Fluxo de Monitoramento
1. Sistema verifica agendamentos a cada 30 segundos
2. Para cada agendamento 'agendado' com horário passado há mais de 20 minutos:
   - Exibe notificação de atenção
   - Mostra modal de confirmação
   - Inicia countdown de 5 minutos
3. Dono pode confirmar presença ou registrar ausência
4. Se não houver resposta em 5 minutos, registra ausência automaticamente

### Interface do Usuário
- **Notificações**: Painel flutuante no canto superior direito
- **Modal**: Interface centralizada para confirmação
- **Countdown**: Temporizador visual mostrando tempo restante
- **Botões**: Ações claras e intuitivas

### Backend
- Novo status 'nao_compareceu' adicionado ao enum StatusAgendamento
- Validação de status atualizada para aceitar o novo status
- API mantém agendamentos no histórico em vez de excluí-los

## Como Testar

### 1. Criar Agendamento de Teste
```bash
cd backend
python create_test_appointment.py
```

### 2. Simular Cenário de Teste
1. Acesse o dashboard do dono
2. Aguarde ou ajuste o horário do agendamento para que passe 20 minutos
3. Sistema deve mostrar notificação automaticamente
4. Teste os botões de confirmação
5. Teste o timeout automático (espere 5 minutos)

### 3. Verificar Status
- Agendamentos confirmados ficam com status 'confirmado'
- Agendamentos não comparecidos ficam com status 'nao_compareceu'
- Todos permanecem no histórico

## Configurações

### Tempos Configuráveis
```javascript
// No arquivo dashboard-dono.html, classe PresenceMonitor
this.gracePeriod = 20 * 60 * 1000; // 20 minutos de tolerância
this.notificationTimeout = 5 * 60 * 1000; // 5 minutos para resposta
this.checkInterval = 30000; // 30 segundos entre verificações
```

### Personalização Visual
- Cores e estilos podem ser ajustados no CSS
- Sons podem ser substituídos por arquivos de áudio
- Layout responsivo para diferentes telas

## Benefícios

1. **Automação**: Reduz trabalho manual de verificação
2. **Precisão**: Registra presença em tempo real
3. **Histórico**: Mantém registro completo de ausências
4. **Interface intuitiva**: Fácil de usar em situações de urgência
5. **Flexibilidade**: Permite intervenção manual quando necessário

## Considerações Técnicas

- **Performance**: Verificações a cada 30 segundos não impactam performance
- **Confiabilidade**: Sistema tolerante a falhas, continua funcionando mesmo com erros
- **Segurança**: Usa APIs existentes, não cria novos endpoints
- **Compatibilidade**: Funciona em navegadores modernos
- **Escalabilidade**: Pode ser facilmente expandido com mais funcionalidades

## Scripts de Manutenção

### 1. Limpeza Manual de Agendamentos Antigos
```bash
cd backend
python cleanup_old_no_shows.py
```
**Remove agendamentos 'nao_compareceu' com mais de 2 dias**

### 2. Atualização de Status de Agendamentos Passados
```bash
cd backend
python update_past_appointments.py
```
**Marca como 'nao_compareceu' agendamentos passados não confirmados**

### 3. Criação de Dados de Teste
```bash
cd backend
python test_presence_monitor.py
```
**Cria agendamentos para testar o sistema de presença**

### 4. Migração do Banco de Dados
```bash
cd backend
python migrate_database.py
```
**Apaga todos os dados e recria tabelas com nova estrutura**

## Próximas Melhorizações Possíveis

1. **Notificações push**: Para dispositivos móveis
2. **Relatórios**: Estatísticas de ausência por cliente/serviço
3. **Reagendamento automático**: Sugestão de novos horários
4. **Integração WhatsApp**: Notificações para clientes
5. **Machine Learning**: Previsão de ausência baseada em histórico
6. **API de limpeza**: Endpoint REST para limpeza programada
7. **Dashboard administrativo**: Interface para configurar parâmetros