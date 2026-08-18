// Supabase Edge Function — Webhook Mercado Pago
// Deploy: supabase functions deploy handle-mercadopago-webhook

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
  // Apenas POST aceito
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const body = await req.json();
    console.log("Webhook recebido:", body);

    // Mercado Pago envia notificações de pagamento
    const { type, data } = body;

    if (type === "payment") {
      const paymentId = data.id;

      // Buscar detalhes do pagamento na API do Mercado Pago
      const paymentResponse = await fetch(
        `https://api.mercadopago.com/v1/payments/${paymentId}`,
        {
          headers: {
            Authorization: `Bearer ${MERCADOPAGO_ACCESS_TOKEN}`,
          },
        }
      );

      if (!paymentResponse.ok) {
        console.error("Erro ao buscar pagamento:", await paymentResponse.text());
        return new Response("Error fetching payment", { status: 500 });
      }

      const payment = await paymentResponse.json();
      console.log("Detalhes do pagamento:", payment);

      const { status, transaction_amount, metadata } = payment;
      const userId = metadata?.user_id; // Enviado no momento da criação do pagamento

      if (!userId) {
        console.error("user_id não encontrado no metadata");
        return new Response("Missing user_id", { status: 400 });
      }

      // Determinar créditos baseado no valor pago
      const amountRounded = Math.round(transaction_amount);
      const creditsMb = CREDIT_PACKAGES[amountRounded] || Math.round(amountRounded * 10); // Fallback: R$ 1 = 10 MB

      // Buscar ou criar transação no Supabase
      const { data: existingTransaction } = await supabase
        .from("transactions")
        .select("*")
        .eq("payment_id", paymentId.toString())
        .single();

      if (existingTransaction) {
        // Atualizar status se mudou
        if (existingTransaction.payment_status !== status) {
          await supabase
            .from("transactions")
            .update({
              payment_status: status,
              approved_at: status === "approved" ? new Date().toISOString() : null,
              payment_metadata: payment,
            })
            .eq("payment_id", paymentId.toString());
        }
      } else {
        // Criar nova transação
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + 90); // 90 dias

        await supabase.from("transactions").insert({
          user_id: userId,
          amount_brl: transaction_amount,
          credits_mb: creditsMb,
          payment_method: "mercadopago",
          payment_id: paymentId.toString(),
          payment_status: status,
          expires_at: expiresAt.toISOString(),
          approved_at: status === "approved" ? new Date().toISOString() : null,
          payment_metadata: payment,
        });
      }

      // Se aprovado, adicionar créditos ao usuário
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

          console.log(`✅ ${creditsMb} MB adicionados para o usuário ${userId}`);
        }
      }

      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ignored: true }), { status: 200 });
  } catch (error) {
    console.error("Erro no webhook:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
