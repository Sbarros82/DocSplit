# Deploy Webhook do Mercado Pago no Supabase

## 📋 Passo a Passo via Painel Web

### 1️⃣ Acessar Edge Functions

1. Acesse: https://supabase.com/dashboard/project/pjryxiwzpfbypawxgios/functions
2. Faça login se necessário

### 2️⃣ Criar Nova Function

1. Clique em **"Create a new function"**
2. **Function name:** `handle-mercadopago-webhook`
3. **Editor:** Cole o código abaixo

### 3️⃣ Código da Function

```typescript
// Supabase Edge Function — Webhook Mercado Pago
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const MERCADOPAGO_ACCESS_TOKEN = Deno.env.get("MERCADOPAGO_ACCESS_TOKEN")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

// Mapa de valores → créditos
const CREDIT_PACKAGES: Record<number, number> = {
  5: 50,      // R$ 5 = 50 MB
  15: 200,    // R$ 15 = 200 MB (bônus 33%)
  30: 500,    // R$ 30 = 500 MB (bônus 67%)
  50: 1000,   // R$ 50 = 1 GB (bônus 100%)
};

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const body = await req.json();
    console.log("Webhook recebido:", body);

    const { type, data } = body;

    if (type === "payment") {
      const paymentId = data.id;

      // Buscar detalhes do pagamento
      const paymentResponse = await fetch(
        `https://api.mercadopago.com/v1/payments/${paymentId}`,
        {
          headers: {
            Authorization: `Bearer ${MERCADOPAGO_ACCESS_TOKEN}`,
          },
        }
      );

      if (!paymentResponse.ok) {
        console.error("Erro ao buscar pagamento");
        return new Response("Error fetching payment", { status: 500 });
      }

      const payment = await paymentResponse.json();
      console.log("Pagamento:", payment);

      const { status, transaction_amount, metadata } = payment;
      const userId = metadata?.user_id;

      if (!userId) {
        return new Response("Missing user_id", { status: 400 });
      }

      // Calcular créditos
      const amountRounded = Math.round(transaction_amount);
      const creditsMb = CREDIT_PACKAGES[amountRounded] || Math.round(amountRounded * 10);

      // Verificar se já existe
      const { data: existingTransaction } = await supabase
        .from("transactions")
        .select("*")
        .eq("payment_id", paymentId.toString())
        .single();

      if (existingTransaction) {
        // Atualizar
        if (existingTransaction.payment_status !== status) {
          await supabase
            .from("transactions")
            .update({
              payment_status: status,
              approved_at: status === "approved" ? new Date().toISOString() : null,
            })
            .eq("payment_id", paymentId.toString());
        }
      } else {
        // Criar
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + 90);

        await supabase.from("transactions").insert({
          user_id: userId,
          amount_brl: transaction_amount,
          credits_mb: creditsMb,
          payment_method: "mercadopago",
          payment_id: paymentId.toString(),
          payment_status: status,
          expires_at: expiresAt.toISOString(),
          approved_at: status === "approved" ? new Date().toISOString() : null,
        });
      }

      // Se aprovado, adicionar créditos
      if (status === "approved") {
        const { data: user } = await supabase
          .from("users")
          .select("total_credits_mb")
          .eq("id", userId)
          .single();

        if (user) {
          await supabase
            .from("users")
            .update({
              total_credits_mb: (user.total_credits_mb || 0) + creditsMb,
            })
            .eq("id", userId);

          console.log(`✅ ${creditsMb} MB adicionados`);
        }
      }

      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ignored: true }), { status: 200 });
  } catch (error) {
    console.error("Erro:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
```

### 4️⃣ Configurar Secrets

Antes de fazer deploy, configure os secrets:

1. No painel do Supabase, vá em **Settings → Edge Functions**
2. Clique em **"Manage secrets"**
3. Adicione:

```
MERCADOPAGO_ACCESS_TOKEN=TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998
SUPABASE_URL=https://pjryxiwzpfbypawxgios.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k
```

### 5️⃣ Deploy

1. Clique em **"Deploy function"**
2. Aguarde o deploy (30 segundos)
3. **Copie a URL** da function (exemplo: `https://pjryxiwzpfbypawxgios.supabase.co/functions/v1/handle-mercadopago-webhook`)

---

## ✅ Depois do Deploy

A URL do webhook será:
```
https://pjryxiwzpfbypawxgios.supabase.co/functions/v1/handle-mercadopago-webhook
```

Essa URL será configurada no painel do Mercado Pago.

---

## 🎯 Próximo Passo

Configurar a URL do webhook no Mercado Pago:
1. Acessar: https://www.mercadopago.com.br/developers/panel/app/2185639579586130
2. Clicar em **"Webhooks"**
3. Adicionar a URL
4. Selecionar eventos: **Payments**
5. Salvar

---

**Me avise quando o deploy terminar e me passe a URL da function!** 🚀
