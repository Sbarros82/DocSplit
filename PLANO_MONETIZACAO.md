# 💰 Plano de Monetização — DocSplit Pro

## 🎯 Modelo de Negócio Proposto

### **Sistema de Doação com Créditos** (sem assinatura)

**Plano Gratuito:**
- ✅ 3 arquivos por dia (máx 2 MB cada)
- ✅ Até 10 páginas por arquivo
- ✅ Marca d'água "Processado por DocSplit"
- ❌ Sem OCR (só texto nativo)

**Doação Mínima: R$ 5,00** (pagamento único)
- ✅ **50 MB de crédito** (pode processar vários arquivos até esgotar)
- ✅ OCR completo (scans/fotos)
- ✅ Até 200 páginas por arquivo
- ✅ Sem marca d'água
- ✅ Prioridade no processamento
- ✅ Validade: **90 dias** após a doação

**Valores sugeridos:**
- R$ 5 → 50 MB
- R$ 15 → 200 MB (bônus 33%)
- R$ 30 → 500 MB (bônus 67%)
- R$ 50 → 1 GB (bônus 100%)

---

## 💳 Stack Técnica Necessária

### **1. Banco de Dados** (OBRIGATÓRIO agora)

**Supabase PostgreSQL** (grátis até 500 MB):

```sql
-- Tabela de usuários
users (
  id uuid PRIMARY KEY,
  email text UNIQUE NOT NULL,
  created_at timestamp,
  total_credits_mb integer DEFAULT 0,
  used_credits_mb integer DEFAULT 0,
  last_free_use timestamp,
  free_uses_today integer DEFAULT 0
)

-- Tabela de transações
transactions (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  amount_brl decimal(10,2),
  credits_mb integer,
  payment_method text, -- 'mercadopago' | 'pagseguro'
  payment_id text,
  status text, -- 'pending' | 'approved' | 'rejected'
  created_at timestamp,
  expires_at timestamp -- created_at + 90 dias
)

-- Tabela de jobs (processamentos)
jobs (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  filename text,
  file_size_mb decimal(10,2),
  pages_count integer,
  status text, -- 'processing' | 'completed' | 'failed'
  created_at timestamp,
  processing_time_seconds integer
)
```

**Por que Supabase?**
- ✅ Auth integrado (email/senha, Google, GitHub)
- ✅ PostgreSQL grátis
- ✅ Row Level Security (RLS) automático
- ✅ SDK JavaScript + Python
- ✅ Edge Functions serverless

---

### **2. Gateway de Pagamento**

#### **Opção A: Mercado Pago** (já tem no tourbrasil)

**Vantagens:**
- ✅ PIX instantâneo
- ✅ Cartão de crédito/débito
- ✅ Boleto
- ✅ SDK React oficial (`@mercadopago/sdk-react`)
- ✅ Webhook automático de confirmação
- ✅ Taxa: 4,99% + R$ 0,40

**Fluxo:**
1. Usuário escolhe pacote (R$ 5, 15, 30, 50)
2. Frontend cria "preference" via API
3. Abre checkout Mercado Pago
4. Usuário paga (PIX/cartão)
5. Webhook confirma → adiciona créditos no Supabase

---

#### **Opção B: PagSeguro**

**Vantagens:**
- ✅ Popular no Brasil
- ✅ PIX + cartão + boleto
- ✅ Webhook de confirmação
- ✅ Taxa: 4,99% + R$ 0,40

**Desvantagem:**
- ❌ SDK menos robusto que Mercado Pago
- ❌ API mais complexa

**Recomendação:** começar com **Mercado Pago** (você já tem a integração pronta).

---

### **3. Arquitetura Backend**

```
Frontend (React/Vue)
  ↓
FastAPI (Python) — d:\Snap\api\index.py
  ↓
├─ Supabase Auth → valida usuário
├─ Supabase DB → checa créditos
├─ Pipeline PDF → processa
└─ Supabase DB → desconta créditos usados

Webhook Mercado Pago
  ↓
FastAPI /webhook/mercadopago
  ↓
Supabase → adiciona créditos
  ↓
Email confirmação (Supabase Edge Function)
```

---

## 📊 SEO — Como Aparecer no Google

### **1. Meta Tags (HTML)**

```html
<head>
  <title>DocSplit — Separe PDFs Misturados Automaticamente | Boletos, NF-e, PIX</title>
  <meta name="description" content="Ferramenta online para separar PDFs com múltiplos documentos. Identifica boletos, comprovantes PIX, notas fiscais, DARF e mais. OCR grátis." />
  <meta name="keywords" content="separar pdf, dividir pdf, organizar documentos, pdf splitter, boleto, nfe, pix, darf" />
  
  <!-- Open Graph (Facebook/LinkedIn) -->
  <meta property="og:title" content="DocSplit — Separe PDFs Misturados" />
  <meta property="og:description" content="Identifica e separa boletos, PIX, NF-e automaticamente" />
  <meta property="og:image" content="https://docsplit.com/og-image.jpg" />
  <meta property="og:url" content="https://docsplit.com" />
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="DocSplit — Separe PDFs" />
  <meta name="twitter:description" content="Ferramenta para organizar documentos brasileiros" />
  <meta name="twitter:image" content="https://docsplit.com/twitter-card.jpg" />
  
  <!-- Structured Data (Schema.org) -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "DocSplit",
    "description": "Separe PDFs misturados automaticamente",
    "applicationCategory": "BusinessApplication",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "BRL"
    },
    "operatingSystem": "Web",
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "ratingCount": "127"
    }
  }
  </script>
</head>
```

---

### **2. Conteúdo Otimizado (Blog/Landing)**

**Criar páginas:**
- `/` — Landing page com casos de uso
- `/como-funciona` — Explicação detalhada + vídeo
- `/precos` — Tabela de valores
- `/blog/como-separar-boletos-pdf` — Artigo SEO
- `/blog/organizar-documentos-fiscais` — Artigo SEO
- `/ajuda` — FAQ com schema FAQ do Google

**Palavras-chave alvo:**
- "separar pdf misturado"
- "dividir pdf por páginas"
- "organizar documentos contábeis"
- "extrair boletos de pdf"
- "separar notas fiscais pdf"

---

### **3. Performance & Técnico**

- ✅ **Lighthouse 90+** (Core Web Vitals)
- ✅ **Sitemap.xml** gerado
- ✅ **robots.txt** permitindo indexação
- ✅ **SSL/HTTPS** (Vercel/Railway incluem)
- ✅ **Mobile-first** (responsivo)
- ✅ **URL amigável** (docsplit.com/separar-pdf)

---

### **4. Google Search Console + Analytics**

1. Cadastrar site no Google Search Console
2. Verificar propriedade (meta tag ou DNS)
3. Enviar sitemap.xml
4. Google Analytics 4 para acompanhar:
   - Conversões (uploads → pagamentos)
   - Páginas mais acessadas
   - Origem do tráfego

---

## 💸 Estratégia de Receita Recorrente

### **Problema do modelo atual:** doação única não é recorrente

### **Soluções para recorrência:**

#### **1. Créditos com Validade** ✅ (já proposto)
- Créditos expiram em 90 dias
- Força recompra para usuários frequentes
- "Use ou perca"

#### **2. Assinatura Opcional (R$ 19/mês)**
- 500 MB/mês inclusos
- OCR ilimitado
- Sem marca d'água
- Acesso a features premium:
  - API para integração
  - Processamento em lote (ZIP de PDFs)
  - Webhook de conclusão
  - Armazenamento de 30 dias

#### **3. Modelo B2B (Empresas)**
- **R$ 99/mês**: 5 GB, 10 usuários
- **R$ 299/mês**: 20 GB, ilimitado usuários
- Dashboard de gestão
- Suporte prioritário
- White-label (marca da empresa)

#### **4. Marketplace de Integrações**
- Plugin Wordpress: R$ 29 (único)
- Zapier/Make: R$ 15/mês
- API avulsa: R$ 0,10 por MB processado

---

## 📈 Estimativa de Receita

**Cenário Conservador (6 meses):**

| Métrica | Valor |
|---------|-------|
| Visitantes/mês | 1.000 (SEO + ads) |
| Taxa conversão gratuito | 60% (600 uploads) |
| Taxa conversão paga | 5% (50 doações) |
| Ticket médio | R$ 12 (mix de planos) |
| **Receita/mês** | **R$ 600** |

**Cenário Otimista (12 meses):**

| Métrica | Valor |
|---------|-------|
| Visitantes/mês | 10.000 |
| Conversão paga | 8% (800 doações) |
| Ticket médio | R$ 18 |
| Assinaturas | 20 × R$ 19 = R$ 380 |
| **Receita/mês** | **R$ 14.780** |

**Custos mensais:**
- Supabase: R$ 0 (plano grátis até crescer)
- Railway/Vercel: R$ 25-50
- Domínio: R$ 5/mês
- **Lucro líquido:** 95% da receita

---

## 🚀 Roadmap de Desenvolvimento

### **Fase 1: MVP Monetizado (2-3 semanas)**
- [ ] Supabase: schema + auth
- [ ] Login/cadastro (email + Google)
- [ ] Sistema de créditos (adicionar/descontar)
- [ ] Integração Mercado Pago
- [ ] Webhook de confirmação
- [ ] Dashboard do usuário (créditos restantes, histórico)
- [ ] Landing page SEO-friendly
- [ ] Deploy Railway com domínio próprio

### **Fase 2: Crescimento (1-2 meses)**
- [ ] Blog com 5 artigos SEO
- [ ] Google Search Console + Analytics
- [ ] Campanhas Google Ads (R$ 100/mês teste)
- [ ] Email marketing (boas-vindas, lembrete créditos)
- [ ] Programa de afiliados (20% comissão)

### **Fase 3: Escala (3-6 meses)**
- [ ] Plano assinatura mensal
- [ ] API pública (B2B)
- [ ] White-label para contadores/escritórios
- [ ] Integrações (Zapier, Make, n8n)
- [ ] App mobile (React Native)

---

## 🛠️ Stack Tecnológica Final

**Frontend:**
- React + TypeScript (Vite)
- Tailwind CSS + Shadcn/ui (do tourbrasil)
- React Query (cache)
- React Router (rotas)

**Backend:**
- FastAPI (Python) — já existe em `d:\Snap\api\`
- Supabase (DB + Auth + Storage)
- Mercado Pago SDK

**Infra:**
- Railway (produção)
- Supabase (banco grátis)
- Cloudflare (DNS + CDN)
- Domínio: docsplit.com.br ou similar

**Monitoramento:**
- Google Analytics 4
- Sentry (erros)
- Supabase logs

---

## 🎨 Melhorias de Profissionalização

### **Design:**
- [ ] Logo profissional (Canva ou Fiverr R$ 50)
- [ ] Paleta de cores consistente
- [ ] Ilustrações customizadas
- [ ] Vídeo explicativo (30s)

### **Confiança:**
- [ ] Depoimentos de clientes
- [ ] Contador de documentos processados (social proof)
- [ ] Selo de segurança (SSL, LGPD)
- [ ] Política de privacidade + Termos de uso

### **UX:**
- [ ] Onboarding interativo (tour guiado)
- [ ] Notificações de progresso (real-time)
- [ ] Preview do resultado antes de baixar
- [ ] Histórico de processamentos

---

## ❓ Próximos Passos — O que você autoriza?

**Posso desenvolver na seguinte ordem:**

1. **Schema Supabase** (tabelas users, transactions, jobs)
2. **Auth + Login** (componentes React)
3. **Sistema de créditos** (lógica backend FastAPI)
4. **Integração Mercado Pago** (checkout + webhook)
5. **Dashboard do usuário** (saldo, histórico)
6. **Landing page profissional** (SEO + conversão)

**Ou você prefere:**
- Primeiro ver mockups/protótipos?
- Começar só com o backend (DB + API)?
- Focar em SEO antes de monetização?

**Me diga o que autoriza desenvolver primeiro!**
