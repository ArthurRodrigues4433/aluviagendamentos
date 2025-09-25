# Dashboard Real-Time Update System

Sistema completo para atualização em tempo real do dashboard administrativo após operações PUT, POST ou DELETE no back-end.

## 📋 Visão Geral

Este sistema permite que o dashboard administrativo se atualize automaticamente sempre que dados são alterados no back-end, garantindo que as informações exibidas estejam sempre sincronizadas sem necessidade de recarregar a página.

## 🚀 Funcionalidades

- ✅ **Atualização automática** após operações CRUD
- ✅ **Formatação de datas** no formato DD/MM/AAAA
- ✅ **Cálculo de dias restantes** com cores de alerta
- ✅ **Badges dinâmicos** (verde/vermelho/amarelo) baseados em status
- ✅ **Funções reutilizáveis** para diferentes tipos de dados
- ✅ **Interceptadores automáticos** para detectar mudanças
- ✅ **Atualização seletiva** (salão específico ou dashboard completo)

## 📁 Arquivos Criados

1. **`src/frontend/services/dashboard-realtime.js`** - Sistema principal
2. **`src/frontend/services/dashboard-realtime-examples.js`** - Exemplos de integração
3. **`DASHBOARD_REALTIME_README.md`** - Esta documentação

## 🛠️ Instalação

### 1. Incluir os Scripts

Adicione no final do `<body>` do `dashboard-admin.html`:

```html
<!-- Sistema de atualização em tempo real -->
<script src="/frontend/services/dashboard-realtime.js"></script>
<!-- Exemplos de integração (opcional) -->
<script src="/frontend/services/dashboard-realtime-examples.js"></script>
```

### 2. Verificar Dependências

Certifique-se de que estes scripts já estão incluídos:
- `/frontend/config.js`
- `/frontend/app.js`

## 📖 Como Usar

### Uso Básico

O sistema inicializa automaticamente. Para operações simples, use o wrapper `performDataOperation`:

```javascript
// Exemplo: Atualizar mensalidade
await window.DashboardRealtime.performDataOperation(async () => {
    return await api.request(`/salons/admin/${salonId}/subscription`, {
        method: 'PUT',
        body: JSON.stringify({
            mensalidade_pago: true,
            data_vencimento: '2024-12-31'
        })
    });
}, {
    refreshSalonId: salonId // Atualiza apenas este salão
});
```

### Atualização Manual

```javascript
// Atualizar dashboard completo
await window.DashboardRealtime.refreshDashboard();

// Atualizar apenas estatísticas
await window.DashboardRealtime.refreshStats();

// Atualizar apenas tabela de salões
await window.DashboardRealtime.refreshSalonsList();

// Atualizar apenas mensalidades
await window.DashboardRealtime.refreshSubscriptionsList();
```

### Funções Utilitárias

```javascript
// Formatar data
const formattedDate = window.DashboardRealtime.formatDate('2024-12-31');
// Resultado: "31/12/2024"

// Calcular dias restantes
const daysInfo = window.DashboardRealtime.calculateDaysRemaining('2024-12-31');
// Resultado: { text: "10 dias", class: "" }

// Atualizar badge
window.DashboardRealtime.updateStatusBadge('statusBadge', true, 'Pago', 'Pendente');

// Atualizar contador
window.DashboardRealtime.updateCounter('totalSalons', 25, '', ' salões');
```

## 🔧 Integração com Operações Existentes

### Modificar handleSubscriptionSubmit

Substitua a função existente por:

```javascript
async function handleSubscriptionSubmit(event) {
    event.preventDefault();

    const paymentStatus = document.getElementById('paymentStatus').value === 'true';
    const dueDate = document.getElementById('dueDate').value;

    if (!dueDate) {
        UI.showError('Data de vencimento é obrigatória');
        return;
    }

    try {
        const result = await window.DashboardRealtime.performDataOperation(async () => {
            return await api.request(`/salons/admin/${currentSalonId}/subscription`, {
                method: 'PUT',
                body: JSON.stringify({
                    mensalidade_pago: paymentStatus,
                    data_vencimento: dueDate
                })
            });
        }, {
            refreshSalonId: currentSalonId
        });

        if (result.success) {
            UI.showSuccess('Mensalidade atualizada com sucesso!');
            closeSubscriptionModal();
        } else {
            UI.showError(result.error || 'Erro ao atualizar mensalidade');
        }
    } catch (error) {
        console.error('Erro ao atualizar mensalidade:', error);
        UI.showError('Erro ao atualizar mensalidade');
    }
}
```

### Modificar handleSalonSubmit

```javascript
async function handleSalonSubmit(event) {
    event.preventDefault();

    const name = document.getElementById('salonName').value.trim();
    const email = document.getElementById('salonEmail').value.trim();

    if (!name) {
        UI.showError('Nome do salão é obrigatório');
        return;
    }

    try {
        const result = await window.DashboardRealtime.performDataOperation(async () => {
            return await api.request('/salons/admin/create', {
                method: 'POST',
                body: JSON.stringify({
                    nome: name,
                    email: email || undefined
                })
            });
        }, {
            refresh: true // Refresh completo após criar salão
        });

        if (result.success) {
            UI.showSuccess('Salão criado com sucesso!');
            closeSalonModal();
        } else {
            UI.showError(result.error || 'Erro ao criar salão');
        }
    } catch (error) {
        console.error('Erro ao criar salão:', error);
        UI.showError('Erro ao criar salão');
    }
}
```

## 🎨 Sistema de Cores para Status

### Badges de Status
- **Verde (`badge-success`)**: Ativo, Pago, Confirmado, Concluído
- **Vermelho (`badge-danger`)**: Inativo, Pendente, Cancelado
- **Amarelo (`badge-warning`)**: Pendente, Não Compareceu
- **Azul (`badge-info`)**: Agendado

### Cores de Dias Restantes
- **Vermelho (`text-danger`)**: Vencido (dias negativos)
- **Amarelo (`text-warning`)**: Vence hoje ou em até 7 dias
- **Normal**: Mais de 7 dias para vencer

## 📊 Seções Suportadas

### Atualizadas Automaticamente
- ✅ **Estatísticas Gerais** (`adminStatsGrid`)
- ✅ **Salões Recentes** (`recentSalons`)
- ✅ **Lista de Salões** (`salonsList`)
- ✅ **Lista de Mensalidades** (`subscriptionsList`)
- ✅ **Lista de Donos** (`ownersList`)

### Placeholder para Futuras Implementações
- 🔄 **Próximos Agendamentos** (`upcomingAppointments`)
- 🔄 **Agendamentos Pendentes** (`pendingAppointments`)
- 🔄 **Histórico de Serviços** (`serviceHistory`)

## 🔍 Debugging

### Logs do Sistema
O sistema registra logs detalhados no console:

```
[REALTIME] Inicializando sistema de atualização em tempo real...
[REALTIME] Detectada operação que altera dados: PUT
[REALTIME] Atualizando dashboard completo...
[REALTIME] Dashboard atualizado com sucesso
```

### Verificar Status
```javascript
console.log('Sistema inicializado:', window.DashboardRealtime.initialized);
console.log('Instância do sistema:', window.DashboardRealtime);
```

## 🚀 Recursos Avançados

### Interceptadores Personalizados

Para APIs sem interceptadores nativos:

```javascript
// Interceptar fetch global
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const result = await originalFetch.apply(this, args);

    const url = args[0];
    if (typeof url === 'string' && url.includes('/salons/admin/')) {
        if (args[1]?.method && ['POST', 'PUT', 'DELETE'].includes(args[1].method)) {
            setTimeout(() => {
                window.DashboardRealtime.refreshDashboard();
            }, 300);
        }
    }

    return result;
};
```

### Atualização Condicional

```javascript
// Atualizar apenas se operação foi bem-sucedida
const result = await api.request('/some/endpoint', { method: 'POST' });
if (result.success) {
    await window.DashboardRealtime.refreshDashboard();
}
```

### Callbacks Personalizados

```javascript
// Executar callback após atualização
await window.DashboardRealtime.performDataOperation(async () => {
    return await api.request('/endpoint', { method: 'PUT', body: data });
}, {
    refresh: true
}).then(() => {
    // Callback personalizado
    console.log('Atualização concluída');
    // Executar ações adicionais...
});
```

## 📈 Performance

### Otimizações Implementadas
- **Atualização seletiva**: Só atualiza o necessário
- **Debouncing**: Evita múltiplas atualizações simultâneas
- **Lazy loading**: Carrega dados sob demanda
- **Cache inteligente**: Reutiliza dados quando possível

### Monitoramento
```javascript
// Verificar performance
console.time('dashboard-refresh');
await window.DashboardRealtime.refreshDashboard();
console.timeEnd('dashboard-refresh');
```

## 🧪 Como Testar o Sistema

### 1. Botão de Teste Integrado
No dashboard-admin.html foi adicionado um botão "🧪 Testar Atualização em Tempo Real" na seção de alertas. Clique nele para testar o sistema.

### 2. Teste Manual via Console
```javascript
// Testar atualização completa
await window.DashboardRealtime.refreshDashboard();

// Testar atualização de estatísticas
await window.DashboardRealtime.refreshStats();

// Testar atualização de salões
await window.DashboardRealtime.refreshSalonsList();

// Testar atualização de mensalidades
await window.DashboardRealtime.refreshSubscriptionsList();
```

### 3. Verificar Logs
Abra o console do navegador (F12) e procure por logs com o prefixo `[REALTIME]`.

## 🐛 Troubleshooting

### Problema: Dados não atualizam
**Solução**: Verificar se o endpoint retorna `{ success: true }`

### Problema: Erro "api is not defined"
**Solução**: Garantir que `/frontend/app.js` está carregado antes

### Problema: Atualização muito lenta
**Solução**: Usar `refreshSalonId` em vez de `refresh: true`

### Problema: Múltiplas atualizações
**Solução**: O sistema já inclui debouncing automático

### Problema: "N/A" aparecendo nos campos
**Solução**: Verificar se os dados estão sendo retornados corretamente do backend. Os campos podem aparecer como "N/A" se:
- O campo não existe nos dados retornados
- O campo é null/undefined
- Há erro na formatação da data

## 🔮 Futuras Expansões

### Funcionalidades Planejadas
- [ ] **WebSockets** para atualização em tempo real
- [ ] **Notificações push** para mudanças importantes
- [ ] **Histórico de mudanças** com undo/redo
- [ ] **Filtros avançados** com atualização automática
- [ ] **Gráficos dinâmicos** que se atualizam
- [ ] **Cache local** com sincronização

### Novos Endpoints Necessários
```javascript
// Para agendamentos admin
GET /appointments/admin/upcoming
GET /appointments/admin/pending
GET /appointments/admin/history

// Para estatísticas avançadas
GET /admin/stats/detailed
GET /admin/reports/realtime
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs do console
2. Consultar exemplos em `dashboard-realtime-examples.js`
3. Testar com operações simples primeiro

## 📝 Licença

Este código é parte do projeto Aluvi e segue as mesmas licenças.